# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class ScriptTest(TransactionCase):

    def test_run_python(self):
        script = self.env['smile.script'].create({
            'name': 'TestPython',
            'type': 'python',
            'description': 'Test Python',
            'code': "result = tools.ustr(self.env['res.partner'].search([]))",
        })
        script.with_context(do_not_use_new_cursor=True).run_test()
        self.assertTrue(script.intervention_ids[0].state == 'done')

    def test_run_sql(self):
        script = self.env['smile.script'].create({
            'name': 'TestSQL',
            'type': 'sql',
            'description': 'Test SQL',
            'code': "SELECT 'hello,' || 'world !';",
        })
        script.with_context(do_not_use_new_cursor=True).run_test()
        self.assertTrue(script.intervention_ids[0].state == 'done')

    def test_run_xml(self):
        script = self.env['smile.script'].create({
            'name': 'TestXML',
            'type': 'xml',
            'description': 'Test XML',
            'code': """
            <openerp>
                <data>
                    <menuitem id="menu_test"
                              parent="base.menu_custom"
                              name="Test"/>
                </data>
            </openerp>""",
        })
        script.with_context(do_not_use_new_cursor=True).run_test()
        self.assertTrue(script.intervention_ids[0].state == 'done')
