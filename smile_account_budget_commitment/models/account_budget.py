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

from openerp import api, fields, models, tools, _
from openerp.exceptions import Warning

import openerp.addons.decimal_precision as dp


class BudgetLine(models.Model):
    _inherit = 'crossovered.budget.lines'

    @api.multi
    def _get_sql_query(self, journal_clause, analytic_account_id, date_from, date_to, acc_ids):
        sql_string = "SELECT SUM(al.amount) "\
                     "FROM account_analytic_line al "\
                     "LEFT JOIN account_analytic_journal aj ON al.journal_id = aj.id "\
                     "WHERE al.account_id=%s "\
                     "AND (al.date between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd')) "\
                     "AND al.general_account_id=ANY(%s)" + journal_clause
        sql_args = (analytic_account_id, date_from, date_to, acc_ids)
        return sql_string, sql_args

    @api.multi
    def _prac_amt(self, commitment=False):
        res = {}
        result = 0.0
        context = self._context or {}
        journal_clause = " AND aj.type %s 'general'" % (commitment and '=' or '<>')
        for line in self:
            acc_ids = [x.id for x in line.general_budget_id.account_ids]
            if not acc_ids:
                raise Warning(_("The Budget '%s' has no accounts!") % tools.ustr(line.general_budget_id.name))
            date_to = line.date_to
            date_from = line.date_from
            if 'wizard_date_from' in context:
                date_from = context['wizard_date_from']
            if 'wizard_date_to' in context:
                date_to = context['wizard_date_to']
            if line.analytic_account_id.id:
                sql_string, sql_args = self._get_sql_query(journal_clause, line.analytic_account_id.id,
                                                           date_from, date_to, acc_ids)
                self._cr.execute(sql_string, sql_args)
                result = self._cr.fetchone()[0]
            if result is None:
                result = 0.0
            res[line.id] = result
        return res

    @api.one
    def _commitment_amt(self):
        self.commitment_amount = self._prac_amt(commitment=True)[self.id]
        self.available_amount = self.planned_amount - self.commitment_amount

    analytic_line_ids = fields.One2many('account.analytic.line', 'budget_line_id', 'Analytic Lines')
    commitment_amount = fields.Float('Commitment Amount', digits=dp.get_precision('Account'), compute="_commitment_amt")
    available_amount = fields.Float('Available Amount', digits=dp.get_precision('Account'), compute="_commitment_amt")

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False, lazy=True):
        fields_to_compute = []
        for field in ('commitment_amount', 'available_amount', 'practical_amount', 'theoritical_amount'):
            if field in fields:
                fields.remove(field)
                fields_to_compute.append(field)
        res = super(BudgetLine, self).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby, lazy)
        if fields_to_compute:
            for group in res:
                if group.get('__domain'):
                    line_infos = self.search_read(cr, uid, group['__domain'], fields_to_compute, context=context)
                    for field in fields_to_compute:
                        group[field] = sum([l[field] for l in line_infos])
        return res

    @api.multi
    def action_open_analytic_lines(self):
        self.ensure_one()
        return {
            'name': _('Analytic Lines'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.analytic.line',
            'target': 'new',
            'domain': [('id', 'in', self[0].analytic_line_ids._ids)],
            'context': self._context,
        }


class BudgetPositionCommitmentLimit(models.Model):
    _name = 'account.budget.post.commitment_limit'
    _description = 'Budgetary Position Commitment Limit'
    _rec_name = 'budget_post_id'

    budget_post_id = fields.Many2one('account.budget.post', 'Budgetary Position', required=True, index=True)
    user_id = fields.Many2one('res.users', 'User', required=True, index=True)
    amount_limit = fields.Float('Commitment Amount Limit', digits=dp.get_precision('Account'), required=True)


class BudgetPosition(models.Model):
    _inherit = 'account.budget.post'

    commitment_limit_ids = fields.One2many('account.budget.post.commitment_limit', 'budget_post_id', 'Commitment Limits')
