# -*- coding: utf-8 -*-
# (C) 2011 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestChecklist(TransactionCase):

    def test_create_cron(self):
        """
            This test relies on demo checklist smile_checklist.cron_checklist.
            The checklist activates crons only if active is true.
            I create a cron with null number of calls.
            I check that the cron is inactive.
            I set a number of calls to the cron.
            I check that the cron is active.
        """
        cron = self.env['ir.cron'].create({
            'name': 'Demo cron',
            'model_id': self.env.ref('base.model_res_partner').id,
            'numbercall': 0,
        })
        cron.toggle_active()
        self.assertFalse(
            cron.active,
            'Cron is active.')
        cron.numbercall = 1
        cron.toggle_active()
        self.assertTrue(
            cron.active,
            'Cron is inactive.')
        cron.numbercall = 0
        cron.toggle_active()
        self.assertFalse(
            cron.active,
            'Cron is active.')
