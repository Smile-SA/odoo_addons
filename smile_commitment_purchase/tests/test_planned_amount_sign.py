# -*- coding: utf-8 -*-
# (C) 2014 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import time

from odoo.tests.common import TransactionCase


class PlannedAmountSignTest(TransactionCase):

    def setUp(self):
        super(PlannedAmountSignTest, self).setUp()
        self.purchase = self.env.ref('purchase.purchase_order_3')
        self.budget = self.env.ref(
            'account_budget.crossovered_budget_budgetoptimistic0')
        self.analytic_account = self.env.ref('analytic.analytic_seagate_p2')
        self.budget_post = self.env.ref(
            'smile_commitment_base.account_budget_post_purchase0')
        self.budget_post.account_ids = self.purchase.order_line[0]. \
            product_id.categ_id.property_account_expense_categ_id.ids
        self.budget_limit = self.env.ref(
            'smile_commitment_base.commitment_limit0')

    def test_calculation_depends_planned_amount_sign(self):
        """
        I create settings with planned_amount-sign positive.
        I create a budget line with a positive planned amount.
        I confirm a purchase order of 255.
        the commitment amount is 255 and the available amount is 745.
        I cancel the order.
        commitment amount is 0 and the available amount is 1000.
        I update the settings to chosse a negative planned amount.
        I reconfirm the purchase order.
        The commitment amount is -255 and the available amount is -745.

        """
        self.env['res.config.settings'].create({})
        self.env['ir.config_parameter'].sudo().set_param(
            "planned_amount_sign", 'positive')
        self.budget_line = self.env['crossovered.budget.lines'].create({
            'crossovered_budget_id': self.budget.id,
            'analytic_account_id': self.analytic_account.id,
            'general_budget_id': self.budget_post.id,
            'date_from': time.strftime('%Y-01-01'),
            'date_to': time.strftime('%Y-12-31'),
            'planned_amount': 1000.0,
        })
        self.env['account.analytic.line'].search([]).unlink()
        self.purchase.order_line.write({
            'account_analytic_id': self.analytic_account.id,
        })
        self.purchase.button_confirm()
        self.assertEquals(self.budget_line.commitment_amount, 255.0)
        self.assertEquals(self.budget_line.available_amount, 745.0)
        self.purchase.button_cancel()
        self.assertEquals(self.budget_line.commitment_amount, 0.0)
        self.assertEquals(self.budget_line.available_amount, 1000.0)
        self.env['ir.config_parameter'].sudo().set_param(
            "planned_amount_sign", 'negative')
        self.env['account.analytic.line'].search([]).unlink()
        self.purchase.order_line.write({
            'account_analytic_id': self.analytic_account.id,
        })
        self.budget_line.write({
            'planned_amount': -1000.0,
        })
        self.purchase.button_confirm()
        self.assertEquals(self.budget_line.commitment_amount, -255.0)
        self.assertEquals(self.budget_line.available_amount, -745.0)
