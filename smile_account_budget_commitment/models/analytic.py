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

from openerp import api, fields, models, _
from openerp.exceptions import Warning


class AnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.one
    @api.depends('account_id', 'general_account_id', 'date')
    def _get_budget_line(self):
        if not self.exists():
            return
        if not self.general_account_id:
            self.budget_line_id = False
        else:
            budget_line = self.env['crossovered.budget.lines'].search([
                ('analytic_account_id', '=', self.account_id.id),
                ('general_budget_id.account_ids', 'in', self.general_account_id.id),
                ('date_from', '<=', self.date),
                ('date_to', '>=', self.date),
            ], limit=1)
            self.budget_line_id = budget_line

    budget_line_id = fields.Many2one('crossovered.budget.lines', 'Budget Line', compute='_get_budget_line', store=True)

    @api.one
    @api.constrains('budget_line_id', 'amount')
    def _check_budget_availability(self):
        if self.budget_line_id and self.budget_line_id.available_amount < 0.0:
            raise Warning(_("Available amount [%s%s] is exceeded for the budget line '%s'")
                          % (abs(self.budget_line_id.available_amount),
                             self.budget_line_id.company_id.currency_id.symbol, self.display_name))

    @api.one
    @api.constrains('user_id', 'budget_line_id', 'amount')
    def _check_commitment_limit(self):
        if self.budget_line_id:
            self.user_id.check_commitment_limit(self.budget_line_id.general_budget_id.id, self.amount)
