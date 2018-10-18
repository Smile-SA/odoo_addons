# -*- coding: utf-8 -*-
# (C) 2014 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from math import copysign

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    budget_line_id = fields.Many2one(
        'crossovered.budget.lines', 'Budget Line',
        compute='_get_budget_line', store=True)
    commitment_account_id = fields.Many2one(
        'account.account', 'Commitment Account',
        ondelete='restrict',
        domain=[('deprecated', '=', False)])

    @api.one
    @api.constrains
    def _check_accounts(self):
        if not self.general_account_id and not self.commitment_account_id:
            raise ValidationError(
                _('Commitment account is required '
                  'if general account is not set.'))

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
        if self.budget_line_id:
            sign = copysign(1, self.budget_line_id.planned_amount)
            if self.budget_line_id.available_amount * sign < 0.0:
                raise UserError(
                    _("Available amount [%s%s] is exceeded "
                      "for the budget line '%s'")
                    % (abs(self.budget_line_id.available_amount),
                       self.budget_line_id.company_id.currency_id.symbol,
                       self.budget_line_id.display_name))

    @api.one
    @api.constrains('user_id', 'amount', 'account_id',
                    'commitment_account_id', 'date')
    def _check_commitment_limit(self):
        if self.budget_line_id:
            self.user_id.check_commitment_limit(
                self.budget_line_id.general_budget_id.id, self.amount)
