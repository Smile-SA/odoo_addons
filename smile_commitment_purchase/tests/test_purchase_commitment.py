# -*- coding: utf-8 -*-
# (C) 2014 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import time

from odoo.tests.common import TransactionCase


class PurchaseCommitmentTest(TransactionCase):

    def setUp(self):
        super(PurchaseCommitmentTest, self).setUp()
        self.purchase = self.env.ref('purchase.purchase_order_3')
        budget = self.env.ref(
            'account_budget.crossovered_budget_budgetoptimistic0')
        self.analytic_account = self.env.ref('analytic.analytic_seagate_p2')
        self.budget_post = self.env.ref(
            'smile_commitment_base.account_budget_post_purchase0')
        self.budget_post.account_ids = self.purchase.order_line[0]. \
            product_id.categ_id.property_account_expense_categ_id.ids
        self.budget_limit = self.env.ref(
            'smile_commitment_base.commitment_limit0')
        self.budget_line = self.env['crossovered.budget.lines'].create({
            'crossovered_budget_id': budget.id,
            'analytic_account_id': self.analytic_account.id,
            'general_budget_id': self.budget_post.id,
            'date_from': time.strftime('%Y-01-01'),
            'date_to': time.strftime('%Y-12-31'),
            'planned_amount': -1000.0,
        })
        self.user = self.env.ref('base.user_demo')
        self.user.commitment_global_limit = 1000
        self.budget_limit.amount_limit = 1000
        self.env['account.analytic.line'].search([]).unlink()

    def test_check_budget_available_and_commitment_limit(self):
        """
        I confirm a purchase order of 255.
        I check that the commitment is -255.
        I cancel the order.
        I check that the commitment is 0.
        """
        self.purchase.order_line.write({
            'account_analytic_id': self.analytic_account.id,
        })
        self.purchase.button_confirm()
        self.assertEquals(self.budget_line.commitment_amount, -255.0)
        self.purchase.button_cancel()
        self.assertEquals(self.budget_line.commitment_amount, 0.0)
