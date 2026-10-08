# (C) 2021 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from unittest.mock import patch

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError
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

    def _create_rule(self, **vals):
        values = {
            "name": "Purge old currency rates",
            "model_id": self.model_id.id,
            "field_id": self.field_id.id,
            "use_date_range": True,
            "date_range": 30,
            "date_range_type": "days",
            "batch_size": 100,
        }
        values.update(vals)
        return self.env["purge.data"].create(values)

    def test_03_blocked_record_is_kept(self):
        """
        Je crée deux taux anciens dont un ne peut pas être supprimé
        J'exécute la purge
        Je vérifie que seul le taux supprimable est supprimé et compté
        """
        blocked = self._create_rate(60)
        deletable = self._create_rate(90)
        rule = self._create_rule()
        rate_model = type(self.env["res.currency.rate"])
        orig_unlink = rate_model.unlink

        def _unlink(records):
            if blocked.id in records.ids:
                raise UserError("blocked")
            return orig_unlink(records)

        with patch.object(rate_model, "unlink", _unlink):
            rule.action_purge_records()

        self.assertTrue(blocked.exists())
        self.assertFalse(deletable.exists())
        self.assertEqual(rule.deleted_records, 1)

    def test_04_purge_all_runs_every_active_rule(self):
        """
        Je crée deux règles actives
        J'exécute action_purge_all
        Je vérifie que les deux règles ont purgé
        """
        old_rate = self._create_rate(60)
        rule_1 = self._create_rule()
        rule_2 = self._create_rule(name="Second rule")
        (rule_1 | rule_2).action_purge_records()
        self.assertFalse(old_rate.exists())
        self.assertEqual(rule_1.state, "in_progress")
        self.assertEqual(rule_2.state, "in_progress")

    def test_05_missing_date_range_type_raises(self):
        """
        Je crée une règle sans type de période
        J'exécute la purge
        Je vérifie qu'une erreur est levée et que rien n'est supprimé
        """
        rate = self._create_rate(60)
        rule = self._create_rule(date_range_type=False)
        with self.assertRaises(UserError):
            rule.action_purge_records()
        self.assertTrue(rate.exists())
