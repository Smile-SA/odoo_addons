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
from openerp.exceptions import ValidationError


class PurchaseCommitmentTest(TransactionCase):

    def test_check_budget_available_and_commitment_limit(self):
        import time
        analytic_account = self.env.ref('account.analytic_online')
        budget = self.env.ref('account_budget.crossovered_budget_budgetoptimistic0')
        budget_post = self.env.ref('account_budget.account_budget_post_purchase0')
        purchase = self.env.ref('purchase.purchase_order_3')
        account_id = purchase.order_line[0].product_id.categ_id.property_account_expense_categ.id
        budget_post.write({'account_ids': [(4, account_id)]})
        budget_line = self.env['crossovered.budget.lines'].create({
            'crossovered_budget_id': budget.id,
            'analytic_account_id': analytic_account.id,
            'general_budget_id': budget_post.id,
            'date_from': time.strftime('%Y-01-01'),
            'date_to': time.strftime('%Y-12-31'),
            'planned_amount': 1000.0,
        })
        purchase.order_line.write({'account_analytic_id': analytic_account.id})
        limit = self.env.ref('smile_account_budget_commitment.commitment_limit0')
        limit.amount_limit = 100.0
        self.assertRaises(ValidationError, purchase.wkf_confirm_order)
        limit.amount_limit = 1000.0
        purchase.wkf_confirm_order()
        self.assertTrue(budget_line.commitment_amount == 255.0)
