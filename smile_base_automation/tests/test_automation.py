# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.eu>)
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
        vals = dict(trigger=trigger,
                    code="record.write({'name': record.id})",
                    **kwargs)
        return self.env['base.automation'].create(vals)

    def test_10_automation_on_create(self):
        self.create_trigger('on_create')
        record = self.model.create({'name': 'testCreate'})
        self.assertEquals(record.name, str(record.id))

    def test_20_automation_on_write(self):
        self.create_trigger('on_write')
        record = self.model.create({'name': 'testWrite'})
        record.write({'name': 'testWrite2'})
        self.assertEquals(record.name, str(record.id))

    def test_30_automation_on_other_method(self):
        self.env['base.automation'].store_model_methods(self.model._name)
        method = self.env['ir.model.methods'].search([
            ('model_id', '=', self.model_id),
            ('name', '=', 'get_formview_id'),
        ], limit=1)
        self.create_trigger('on_other_method', method_id=method.id)
        record = self.model.create({'name': 'testOtherMethod'})
        getattr(record, method.name)()
        self.assertEquals(record.name, str(record.id))

    def test_40_automation_on_unlink(self):
        self.create_trigger('on_unlink')
        record = self.model.create({'name': 'testUnlink'})
        record.unlink()
