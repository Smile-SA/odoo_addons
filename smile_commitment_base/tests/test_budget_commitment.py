# -*- coding: utf-8 -*-
# (C) 2014 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import time

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class BudgetCommitmentTest(TransactionCase):

    def setUp(self):
        super(BudgetCommitmentTest, self).setUp()
        budget = self.env.ref(
            'account_budget.crossovered_budget_budgetoptimistic0')
        self.analytic_account = self.env.ref('analytic.analytic_seagate_p2')
        self.budget_post = self.env.ref(
            'smile_commitment_base.account_budget_post_purchase0')
        self.budget_limit = self.env.ref(
            'smile_commitment_base.commitment_limit0')
        self.budget_line = self.env['crossovered.budget.lines'].create({
            'crossovered_budget_id': budget.id,
            'analytic_account_id': self.analytic_account.id,
            'general_budget_id': self.budget_post.id,
            'date_from': time.strftime('%Y-01-01'),
            'date_to': time.strftime('%Y-12-31'),
            'planned_amount': 1000.0,
        })
        self.user = self.env.ref('base.user_demo')
        # Generate invoice and pay it
        invoice = self.env.ref('l10n_generic_coa.demo_invoice_3').copy()
        invoice.invoice_line_ids.write({
            'account_analytic_id': self.analytic_account.id,
        })
        invoice.action_invoice_open()
        invoice.pay_and_reconcile(self.env['account.journal'].search(
            [('type', '=', 'bank')], limit=1), 525)

    def test_check_budget_available_and_commitment_limit(self):
        """
        My global commitment limit is 1000€.
        The budget post limit is 100€.
        I check that I can't create an anlaytic line of 200€.
        I check that I can't set the budget post limit to 1500€ (>1000€).
        I set the budget post limit to 1000€.
        I check that I can create an analytic line of 200€.
        I check that I can't create an analytic line of 1500€.
        """
        self.user.commitment_global_limit = 1000
        self.budget_limit.amount_limit = 100.0
        AnalyticLine = self.env['account.analytic.line'].sudo(self.user)
        vals = {
            'name': 'Commitment Test',
            'account_id': self.analytic_account.id,
            'commitment_account_id': self.budget_post.account_ids[0].id,
            'date': time.strftime('%Y-%m-%d'),
            'user_id': self.user.id,
        }
        with self.assertRaises(ValidationError):
            AnalyticLine.create(dict(vals, amount=200))
        with self.assertRaises(ValidationError):
            self.budget_limit.amount_limit = 1500
        self.budget_limit.amount_limit = 1000
        AnalyticLine.create(dict(vals, amount=200))
        with self.assertRaises(ValidationError):
            AnalyticLine.create(dict(vals, amount=1500))
