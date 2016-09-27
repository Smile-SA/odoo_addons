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

import time

from openerp.tests.common import TransactionCase
from openerp.exceptions import ValidationError


class BudgetCommitmentTest(TransactionCase):

    def setUp(self):
        super(BudgetCommitmentTest, self).setUp()
        budget = self.env.ref('account_budget.crossovered_budget_budgetoptimistic0')
        self.analytic_account = self.env.ref('analytic.analytic_seagate_p2')
        self.budget_post = self.env.ref('smile_account_budget_commitment.account_budget_post_purchase0')
        self.budget_post.account_ids = self.env['account.account'].search([('code', '=', 212100)])
        self.budget_limit = self.env.ref('smile_account_budget_commitment.commitment_limit0')
        self.budget_line = self.env['crossovered.budget.lines'].create({
            'crossovered_budget_id': budget.id,
            'analytic_account_id': self.analytic_account.id,
            'general_budget_id': self.budget_post.id,
            'date_from': time.strftime('%Y-01-01'),
            'date_to': time.strftime('%Y-12-31'),
            'planned_amount': 1000.0,
        })
        self.user = self.env.ref('base.user_demo')
        self.user.commitment_global_limit = 1000
        # Generate invoice and pay it
        invoice = self.env.ref('l10n_generic_coa.demo_invoice_3').copy()
        invoice.invoice_line_ids.write({'account_analytic_id': self.analytic_account.id})
        invoice.signal_workflow('invoice_open')
        invoice.pay_and_reconcile(self.env['account.journal'].search([('type', '=', 'bank')], limit=1), 525)

    def test_check_budget_available_and_commitment_limit(self):
        """
        My global commitment limit is 1000€.
        The budget post limit is 100€.
        I check that I can't create an anlaytic line of 200€.
        I check that I can't set the budget post limit to 1500€ (greater than 1000€).
        I set the budget post limit to 1000€.
        I check that I can create an analytic line of 200€.
        I check that I can't create an analytic line of 1500€.
        """
        vals = {
            'name': 'Commitment Test',
            'commitment_type': 'purchase',
            'account_id': self.analytic_account.id,
            'commitment_account_id': self.budget_post.account_ids[0].id,
            'date': time.strftime('%Y-%m-%d'),
            'user_id': self.user.id,
        }
        self.budget_limit.amount_limit = 100.0
        self.env['account.analytic.line'].sudo(self.user).create(dict(vals, amount=200))
        with self.assertRaisesRegexp(ValidationError, "You cannot define a budget post commitment limit superior "
                                     "to the global limit of this user"):
            self.budget_limit.amount_limit = 1500
        self.budget_limit.amount_limit = 1000
        self.env['account.analytic.line'].sudo(self.user).create(dict(vals, amount=200))
        self.env['account.analytic.line'].sudo(self.user).create(dict(vals, amount=1500))
        self.assertTrue(self.budget_line.commitment_amount)
