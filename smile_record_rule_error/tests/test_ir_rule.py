# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase


class IrRuleTest(TransactionCase):

    def create_rule(self, error_message=False):
        self.env['ir.rule'].create({
            'name': 'Rule' + (error_message or ''),
            'model_id': self.env.ref('base.model_res_partner').id,
            'domain_force': "[(0, '=', 1)]",
            'error_message': error_message,
        })

    def test_access_error(self):
        self.create_rule()
        with self.assertRaises(AccessError):
            self.env['res.partner'].with_user(
                self.env.ref("base.user_demo")).create({'name': 'Test'})

    def test_user_error(self):
        self.create_rule('Test')
        with self.assertRaises(UserError):
            self.env['res.partner'].with_user(
                self.env.ref("base.user_demo")).create({'name': 'Test'})
