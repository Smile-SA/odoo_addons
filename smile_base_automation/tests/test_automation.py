# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo.tests.common import TransactionCase


class ActionRuleTest(TransactionCase):

    def setUp(self):
        super(ActionRuleTest, self).setUp()
        self.model = self.env['ir.ui.menu']
        self.model_id = self.env['ir.model'].search(
            [('name', '=', self.model._name)], limit=1).id
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
        self.model.create({'name': 'testCreate'})
        # record = self.model.create({'name': 'testCreate'})
        # self.assertEquals(record.name, str(record.id))

    def test_20_automation_on_write(self):
        self.create_trigger('on_write')
        record = self.model.create({'name': 'testWrite'})
        record.write({'login': 'test2'})
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
