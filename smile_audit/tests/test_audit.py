from odoo.tests.common import TransactionCase


class TestAudit(TransactionCase):

    def setUp(self):
        super(TestAudit, self).setUp()
        rule_vals = {
            "name": "Audit rule on countries",
            "model_id": self.env.ref("base.model_res_country").id,
            "log_create": True,
        }
        self.env["audit.rule"].create(rule_vals)
        country_vals = {
            "name": "La Terre du milieu",
            "code": "JRR",
        }
        self.country = self.env["res.country"].create(country_vals)

    def test_log_created_on_create(self):
        """A log should be created on creating a country"""
        log = self.env["audit.log"].search(
            [
                ("model_id", "=", self.env.ref("base.model_res_country").id),
                ("method", "=", "create"),
                ("res_id", "=", self.country.id),
            ],
            limit=1,
        )
        self.assertEqual(
            log.name,
            "La Terre du milieu",
            "No audit log after country creation",
        )

    def test_log_created_on_write(self):
        """A log should be created on updating a country"""
        self.country.write({"name": "Mordor"})
        log = self.env["audit.log"].search(
            [
                ("model_id", "=", self.env.ref("base.model_res_country").id),
                ("method", "=", "write"),
                ("res_id", "=", self.country.id),
            ]
        )
        self.assertEqual(
            log.res_id, self.country.id, "No audit log after country updating"
        )

    def test_log_created_on_unlink(self):
        """A log should be created on deleting a country"""
        self.country.unlink()
        log = self.env["audit.log"].search(
            [
                ("model_id", "=", self.env.ref("base.model_res_country").id),
                ("method", "=", "unlink"),
                ("res_id", "=", self.country.id),
            ]
        )
        self.assertEqual(
            log.name, "La Terre du milieu", "No audit log after country unlink"
        )
