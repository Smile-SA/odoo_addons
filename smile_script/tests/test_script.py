# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class ScriptTest(TransactionCase):

    def test_run(self):
        script = self.env['smile.script'].create({
            'name': 'Test',
            'type': 'python',
            'description': 'Test',
            'code': "result = tools.ustr(self.env['res.partner'].search([]))",
        })
        script.with_context(do_not_use_new_cursor=True).run_test()
        self.assertTrue(script.intervention_ids[0].state == 'done')
