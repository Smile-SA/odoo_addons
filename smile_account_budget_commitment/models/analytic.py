# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    budget_line_id = fields.Many2one(
        'crossovered.budget.lines', 'Budget Line',
        compute='_get_budget_line', store=True)
    commitment_type = fields.Selection([
        ('purchase', 'Purchase commitment'),
        ('sale', 'Sale commitment'),
        ('payroll', 'Payroll commitment'),
    ], 'Commitment type',
        help="Analytic line generated from sale, purchase or payroll")
    commitment_account_id = fields.Many2one(
        'account.account', 'Commitment Account',
        ondelete='restrict', readonly=True,
        domain=[('deprecated', '=', False)])

    @api.one
    @api.depends('account_id', 'commitment_account_id', 'date')
    def _get_budget_line(self):
        if not self.exists():
            return
        if not self.commitment_account_id:
            self.budget_line_id = False
        else:
            budget_line = self.env['crossovered.budget.lines'].search([
                ('analytic_account_id', '=', self.account_id.id),
                ('general_budget_id.account_ids', 'in',
                    self.commitment_account_id.id),
                ('date_from', '<=', self.date),
                ('date_to', '>=', self.date),
            ], limit=1)
            self.budget_line_id = budget_line

    @api.one
    @api.constrains('budget_line_id', 'amount')
    def _check_budget_availability(self):
        if self.budget_line_id and self.budget_line_id.available_amount < 0.0:
            raise UserError(
                _("Available amount [%s%s] is exceeded "
                  "for the budget line '%s'")
                % (abs(self.budget_line_id.available_amount),
                   self.budget_line_id.company_id.currency_id.symbol,
                   self.display_name))

    @api.one
    @api.constrains('user_id', 'amount', 'account_id',
                    'commitment_account_id', 'date')
    def _check_commitment_limit(self):
        if self.budget_line_id:
            self.user_id.check_commitment_limit(
                self.budget_line_id.general_budget_id.id, self.amount)
