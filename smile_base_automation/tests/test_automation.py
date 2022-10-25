# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
class ActionRuleTest(TransactionCase):

    def setUp(self):
        super(ActionRuleTest, self).setUp()
        self.model = self.env['ir.ui.menu']
        self.model_id = self.env['ir.model'].search(
            [('model', '=', self.model._name)], limit=1).id
        self.defaults = {
            'name': 'Test',
            'model_id': self.model_id,
            'state': 'code',
        }

    def create_trigger(self, trigger, **kwargs):
        kwargs.update(self.defaults)
        vals = dict(trigger=trigger, code="record.write({'name': record.id})", **kwargs)
        return self.env['base.automation'].create(vals)

    def test_01_execute_cron(self):
        expected_value = True
        run = self.env['ir.actions.server.execution'].execute()
        self.assertEqual(run, expected_value,msg='execute : TEST FAILED !!')

    def test_02_automation_on_create(self):
        exepte_values = len(self.env["base.automation"].search([]))
        self.create_trigger('on_create')
        self.assertGreater(len(self.env["base.automation"].search([])), exepte_values,msg='Create : TEST FAILED !!')

    def test_03_automation_on_write(self):
        self.create_trigger('on_write')
        record = self.model.create({'name': 'testWrite1'})
        exepte_value = record.name
        record.write({'name': 'testWrite2'})
        self.assertNotEqual(record.name, exepte_value)

    def test_04_automation_on_other_method(self):
        self.env['base.automation'].store_model_methods(self.model._name)
        method = self.env['ir.model.methods'].search([
            ('model_id', '=', self.model_id),
            ('name', '=', 'get_formview_id'),
        ], limit=1)
        self.create_trigger('on_other_method', method_id=method.id)
        record = self.model.create({'name': 'testOtherMethod'})
        #getattr(record, 'name')()
        self.assertNotEqual(record.name, str(record.id))

    def test_05_automation_on_unlink(self):
        self.create_trigger('on_unlink')
        record = self.model.create({'name': 'testUnlink'})
        record.unlink()
