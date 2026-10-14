from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError


class TestUxFeedbackModels(TransactionCase):
    def setUp(self):
        super(TestUxFeedbackModels, self).setUp()

        self.performance_id = self.env[
            "ux.performance"].create({"name": "Performance Test"})
        self.conformity_id = self.env[
            "ux.conformity"].create({"name": "Conformity Test"})
        self.satisfaction_id = self.env[
            "ux.satisfaction"].create({"name": "Satisfaction Test"})

    def test_00_ux_feedback_wizard(self):
        wizard = self.env["ux.feedback.wizard"].create({
            "performance_id": self.performance_id.id,
            "conformity_id": self.conformity_id.id,
            "satisfaction_id": self.satisfaction_id.id,
            "feedback": "This is a test feedback from wizard",
            "url": "http://example.com/odoo/test",
        })

        wizard.action_submit_feedback()

        feedback = self.env["ux.feedback"].search(
            [("feedback", "=", "This is a test feedback from wizard")], limit=1)
        self.assertTrue(feedback.exists())
        self.assertEqual(feedback.performance_id.name,
                         "Performance Test")
        self.assertEqual(feedback.conformity_id.name,
                         "Conformity Test")
        self.assertEqual(feedback.satisfaction_id.name,
                         "Satisfaction Test")
        self.assertEqual(feedback.feedback,
                         "This is a test feedback from wizard")
        self.assertEqual(feedback.url, "http://example.com/odoo/test")
        self.assertTrue(feedback.reference.endswith('_test'))


    def test_01_ux_feedback_wizard_without_valid_data(self):
        with self.assertRaises(ValidationError):
            self.env["ux.feedback.wizard"].create({
                "performance_id": None,
                "conformity_id": None,
                "satisfaction_id": None,
                "feedback": "This is a test feedback from wizard",
                "url": "http://example.com/odoo/test",
            })
        wizard = self.env["ux.feedback.wizard"].create({
            "performance_id": self.performance_id.id,
            "conformity_id": None,
            "satisfaction_id": None,
            "feedback": "This is a test feedback from wizard",
            "url": "",
        })
        wizard.action_submit_feedback()

        feedback = self.env["ux.feedback"].search(
            [("feedback", "=", "This is a test feedback from wizard")], limit=1)
        self.assertEqual(feedback.reference,
                         "No Reference")