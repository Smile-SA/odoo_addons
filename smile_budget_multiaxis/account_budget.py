# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv
from tools.translate import _


class BudgetLine(osv.osv):
    _inherit = "crossovered.budget.lines"

    def _prac_amt(self, cr, uid, ids, context=None):
        res = {}
        result = 0.0
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            acc_ids = [x.id for x in line.general_budget_id.account_ids]
            if not acc_ids:
                raise osv.except_osv(_('Error!'), _("The General Budget '%s' has no Accounts!") % str(line.general_budget_id.name))
            date_to = line.date_to
            date_from = line.date_from
            if 'wizard_date_from' in context:
                date_from = context['wizard_date_from']
            if 'wizard_date_to' in context:
                date_to = context['wizard_date_to']

            select_clause = "SELECT SUM(amount) FROM account_analytic_line"
            where_clauses = ["(date between to_date(%s, 'yyyy-mm-dd') AND to_date(%s, 'yyyy-mm-dd'))", "general_account_id=ANY(%s)"]
            params = [date_from, date_to, acc_ids]

            axis_obj = self.pool.get('account.analytic.axis')
            axis_ids = axis_obj.search(cr, uid, [('is_budget_axis', '=', True), ('column_label', 'not in', ('date', 'general_account_id'))])
            if not axis_ids:
                where_clauses.append("account_id=%s")
                params.append(line.analytic_account_id.id)
            else:
                for axis in axis_obj.read(cr, uid, axis_ids, ['column_label'], context):
                    where_clauses.append(axis['column_label'] + "=%s")
                    value = getattr(line, axis['column_label'])
                    params.append(value and value.id or False)

            cr.execute("%s WHERE %s" % (select_clause, ' AND '.join(where_clauses)), tuple(params))
            result = cr.fetchone()[0]

            if result is None:
                result = 0.00
            res[line.id] = result
        return res
BudgetLine()
