# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import datetime

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestAccessControlPeriod(TransactionCase):

    def setUp(self):
        super(TestAccessControlPeriod, self).setUp()

        self.user_profile = self.env['res.users'].create({
            'name': 'Profile',
            'login': 'profile',
            'is_user_profile': True,
            'groups_id': [
                (4, self.env.ref('sales_team.group_sale_manager').id)],
        })

        self.user1 = self.env['res.users'].create({
            'name': 'Demo User1',
            'login': 'demouser1',
            'user_profile_id': self.user_profile.id,
            'date_start': datetime.datetime(2020, 1, 29),
            'date_stop': datetime.datetime(2020, 2, 12)
        })

        self.user2 = self.env['res.users'].create({
            'name': 'Demo User2',
            'login': 'demouser2',
            'user_profile_id': self.user_profile.id,
            'date_start': datetime.datetime(2019, 1, 29),
            'date_stop': datetime.datetime(2019, 2, 12)
        })
        self.sale = self._create_sale_order(self.user2)

    def _create_sale_order(self, user):
        return self.env['sale.order'].with_user(user).create({
            'partner_id': self.env.ref('base.res_partner_2').id,
        })

    def _write_sale_order(self, sale, user):
        return sale.with_user(user).write({
            'payment_term_id': self.env.ref(
                'account.account_payment_term_end_following_month').id,
        })

    def test_Access_Control_Period(self):
        """ Check create user.
        Check create and edit sale order:
        * with user2:t he period of RO at 2020/01/29 to 2020/02/12
        * with user1 : the period of RO at 2019/1/29 to 2019/2/12 => error

        """
        self.assertTrue(self.user1.id)
        self.assertTrue(self.sale.id)
        self._write_sale_order(self.sale, self.user2)
        self.assertTrue(self.sale.payment_term_id.id)
        with self.assertRaises(AccessError):
            self._create_sale_order(self.user1)
            self._write_sale_order(self.env.ref(
                'sale.sale_order_7'), self.user1)
