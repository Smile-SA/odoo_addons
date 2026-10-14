from odoo.tests import TransactionCase
from odoo.exceptions import AccessError


class TestUxFeedbackAccess(TransactionCase):
    def setUp(self):
        super().setUp()
        self.user_group = self.env.ref(
            "smile_ux_feedback.group_ux_feedback_user")
        self.manager_group = self.env.ref(
            "smile_ux_feedback.group_ux_feedback_manager")

        self.performance_id = self.env[
            "ux.performance"].create({"name": "Performance Test"})
        self.conformity_id = self.env[
            "ux.conformity"].create({"name": "Conformity Test"})
        self.satisfaction_id = self.env[
            "ux.satisfaction"].create({"name": "Satisfaction Test"})
        self.manager = self.env['res.users'].create({
            'name': 'Test Manager',
            'login': 'test_manager',
            'group_ids': [(6, 0, [self.manager_group.id])]
        })
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user',
            'group_ids': [(6, 0, [self.user_group.id])]
        })
        self.no_ux_user = self.env['res.users'].create({
            'name': 'No UX User',
            'login': 'no_ux_user',
            'group_ids': []
        })

    def test_00_user_access(self):
        self.env = self.env(user=self.user)
        wizard = self.env["ux.feedback.wizard"].create({
            "performance_id": self.performance_id.id,
            "conformity_id": self.conformity_id.id,
            "satisfaction_id": self.satisfaction_id.id,
            "feedback": "Test Feedback",
            "url": "http://example.com/odoo/test",
        })
        wizard.action_submit_feedback()

        feedback = self.env["ux.feedback"].search(
            [("feedback", "=", "Test Feedback")])
        self.assertTrue(feedback.exists())

        feedback.write({"reference": "Updated Feedback"})
        self.assertEqual(feedback.reference, "Updated Feedback")

        feedback.unlink()
        self.assertFalse(feedback.exists())

    def test_01_manager_access(self):
        self.env = self.env(user=self.manager)
        wizard = self.env["ux.feedback.wizard"].create({
            "performance_id": self.performance_id.id,
            "conformity_id": self.conformity_id.id,
            "satisfaction_id": self.satisfaction_id.id,
            "feedback": "Test Feedback",
            "url": "http://example.com/odoo/test",
        })
        wizard.action_submit_feedback()

        feedback = self.env["ux.feedback"].search([("feedback", "=",
                                                    "Test Feedback")])
        self.assertTrue(feedback.exists())
        with self.assertRaises(AccessError):
            feedback.with_user(self.user).read()
        with self.assertRaises(AccessError):
            feedback.with_user(self.user).write({"feedback": "Hello there."})

        feedback.write({"reference": "Updated Feedback"})
        self.assertEqual(feedback.reference, "Updated Feedback")

        feedback.unlink()
        self.assertFalse(feedback.exists())

    def test_02_configuration_tables(self):
        self.env = self.env(user=self.manager)
        performance = self.env["ux.performance"].create(
            {"name": "New Performance Test"})
        self.assertTrue(performance.exists())
        performance.write({"name": "Updated Performance Test"})
        self.assertEqual(performance.name, "Updated Performance Test")
        performance.unlink()
        self.assertFalse(performance.exists())

        conformity = self.env["ux.conformity"].create(
            {"name": "New Conformity Test"})
        self.assertTrue(conformity.exists())
        conformity.write({"name": "Updated Conformity Test"})
        self.assertEqual(conformity.name, "Updated Conformity Test")
        conformity.unlink()
        self.assertFalse(conformity.exists())

        satisfaction = self.env["ux.satisfaction"].create(
            {"name": "New Satisfaction Test"})
        self.assertTrue(satisfaction.exists())
        satisfaction.write({"name": "Updated Satisfaction Test"})
        self.assertEqual(satisfaction.name,
                         "Updated Satisfaction Test")
        satisfaction.unlink()
        self.assertFalse(satisfaction.exists())

        self.env = self.env(user=self.user)
        with self.assertRaises(AccessError):
            self.env["ux.performance"].create(
                {"name": "New Performance Test"})
        with self.assertRaises(AccessError):
            self.performance_id.with_user(self.user).write({"name": "Updated Performance Test"})
        with self.assertRaises(AccessError):
            self.performance_id.with_user(self.user).unlink()

        with self.assertRaises(AccessError):
            self.env["ux.conformity"].create(
                {"name": "New Conformity Test"})
        with self.assertRaises(AccessError):
            self.conformity_id.with_user(self.user).write({"name": "Updated Conformity Test"})
        with self.assertRaises(AccessError):
            self.conformity_id.with_user(self.user).unlink()

        with self.assertRaises(AccessError):
            self.env["ux.satisfaction"].create(
                {"name": "New Satisfaction Test"})
        with self.assertRaises(AccessError):
            self.satisfaction_id.with_user(self.user).write({"name": "Updated Satisfaction Test"})
        with self.assertRaises(AccessError):
            self.satisfaction_id.with_user(self.user).unlink()

    def test_03_no_ux_access(self):
        self.env = self.env(user=self.no_ux_user)
        with self.assertRaises(AccessError):
            self.env["ux.feedback.wizard"].create({
                "reference": "Test Feedback",
                "performance_id": self.performance_id.id,
                "conformity_id": self.conformity_id.id,
                "satisfaction_id": self.satisfaction_id.id,
            })
