# (C) 2021 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestPurgeData(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.currency = cls.env["res.currency"].create(
            {
                "name": "TS1",
                "symbol": "T$",
            }
        )
        cls.model_id = cls.env["ir.model"]._get("res.currency.rate")
        cls.field_id = cls.env["ir.model.fields"].search(
            [
                ("model", "=", "res.currency.rate"),
                ("name", "=", "name"),
            ],
            limit=1,
        )

    def _create_rate(self, days_ago):
        return self.env["res.currency.rate"].create(
            {
                "currency_id": self.currency.id,
                "name": fields.Date.today() - relativedelta(days=days_ago),
                "rate": 2.0,
            }
        )

    def test_01_purge_by_date_range_deletes_only_old_records(self):
        """
        Je crée des taux de change vieux de plus de 30 jours
        Je crée des taux de change vieux de moins de 30 jours
        Je crée une règle de purge sur 30 jours
        J'exécute la purge
        Je vérifie que seuls les taux trop anciens ont été supprimés
        """
        old_rates = self._create_rate(60) | self._create_rate(90)
        recent_rates = self._create_rate(5) | self._create_rate(10)

        rule = self.env["purge.data"].create(
            {
                "name": "Purge old currency rates",
                "model_id": self.model_id.id,
                "field_id": self.field_id.id,
                "use_date_range": True,
                "date_range": 30,
                "date_range_type": "days",
                "batch_size": 100,
            }
        )
        rule.action_purge_records()

        self.assertFalse(old_rates.exists())
        self.assertEqual(recent_rates.exists(), recent_rates)
        self.assertEqual(rule.deleted_records, 2)
        self.assertEqual(rule.state, "in_progress")

    def test_02_action_purge_all_skips_inactive_rule(self):
        """
        Je crée une règle de purge inactive
        J'exécute action_purge_all
        Je vérifie qu'aucun enregistrement n'est supprimé
        """
        old_rate = self._create_rate(60)
        self.env["purge.data"].create(
            {
                "name": "Inactive purge rule",
                "active": False,
                "model_id": self.model_id.id,
                "field_id": self.field_id.id,
                "use_date_range": True,
                "date_range": 30,
                "date_range_type": "days",
                "batch_size": 100,
            }
        )

        self.env["purge.data"].action_purge_all()

        self.assertTrue(old_rate.exists())

    def test_03_dry_run_unlink_does_not_delete(self):
        """
        Je crée un enregistrement
        J'appelle unlink() avec dry_run=True dans le contexte
        Je vérifie que l'enregistrement existe toujours
        J'appelle unlink() sans dry_run
        Je vérifie que l'enregistrement est bien supprimé
        """
        rate = self._create_rate(1)

        result = rate.with_context(dry_run=True).unlink()

        self.assertEqual(result, rate)
        self.assertTrue(rate.exists())

        rate.unlink()

        self.assertFalse(rate.exists())
