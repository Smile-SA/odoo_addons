# -*- encoding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestChecklist(TransactionCase):

    def test_create_cron(self):
        """
            This test relies on demo checklist smile_checklist.cron_checklist.
            The checklist activates crons only if their model is filled.
            I create a cron without model.
            I check that the cron is inactive.
            I assign a model to the cron.
            I check that the cron is active.
        """
        cron = self.env['ir.cron'].create({'name': 'Demo cron'})
        self.assertFalse(
            cron.active, 'Cron is active whereas the Object is not filled.')
        cron.model = 'some.model'
        self.assertTrue(
            cron.active, 'Cron is inactive whereas the Object is filled.')
