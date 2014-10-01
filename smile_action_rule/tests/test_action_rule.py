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

from openerp.tests.common import TransactionCase


class ActionRuleTest(TransactionCase):

    def setUp(self):
        super(ActionRuleTest, self).setUp()
        self.model = self.env['res.users']
        self.model_id = self.ref('base.model_res_users')
        self.defaults = {
            'name': 'Test',
            'model_id': self.model_id,
            'act_user_id': self.uid,
            'act_followers': [(6, 0, [self.ref('base.res_partner_1')])],
        }

    def create_action_rule(self, kind, **kwargs):
        kwargs.update(self.defaults)
        vals = dict(kind=kind, **kwargs)
        return self.env['base.action.rule'].create(vals)

    def test_10_action_rule_on_create(self):
        self.create_action_rule('on_create')
        self.model.create({'name': 'testCreate', 'login': 'testCreate'})

    def test_20_action_rule_on_write(self):
        self.create_action_rule('on_write')
        record = self.model.create({'name': 'testWrite', 'login': 'testWrite'})
        record.write({'login': 'test2'})

    def test_30_action_rule_on_other_method(self):
        self.registry('base.action.rule').onchange_model_id(self.cr, self.uid, None, self.model_id)
        method_ids = self.env['ir.model.methods'].search([('model_id', '=', self.model_id),
                                                          ('name', '=', 'preference_save')], limit=1)._ids
        self.create_action_rule('on_other_method', method_id=method_ids[0])
        record = self.model.create({'name': 'testOtherMethod', 'login': 'testOtherMethod'})
        record.preference_save()

    def test_40_action_rule_on_unlink(self):
        self.create_action_rule('on_unlink')
        record = self.model.create({'name': 'testUnlink', 'login': 'testUnlink'})
        record.unlink()
