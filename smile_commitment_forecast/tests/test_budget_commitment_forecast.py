# -*- coding: utf-8 -*-

import time

from odoo.tests.common import TransactionCase


class BudgetCommitmentForecastTest(TransactionCase):

    def setUp(self):
        super(BudgetCommitmentForecastTest, self).setUp()
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

    def test_check_budget_forecast_available_amount(self):
        """
        My global commitment limit is 1000€.
        I create a analytic line of type forecast with an amount of 200€.
        I check the forecast available amount is equal to 800€.
        """
        self.env['account.analytic.line'].sudo(self.user).create({
            'name': 'Commitment Test',
            'account_id': self.analytic_account.id,
            'commitment_account_id': self.budget_post.account_ids[0].id,
            'date': time.strftime('%Y-%m-%d'),
            'user_id': self.user.id,
            'amount': 200.0,
        })
        self.assertEquals(self.budget_line.forecast_available_amount, 800)
