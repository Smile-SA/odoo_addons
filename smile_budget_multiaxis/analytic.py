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

from osv import osv, fields


class AnalyticAxis(osv.osv):
    _inherit = 'account.analytic.axis'

    _columns = {
        'is_budget_axis': fields.boolean('Budget Axis'),
    }

    def _update_analytic_line_columns(self, cr, ids=None, context=None):
        super(AnalyticAxis, self)._update_analytic_line_columns(cr, ids, context)

        context = context or {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not ids:
            ids = self.search(cr, 1, [], context={'active_test': False})

        line_obj = self.pool.get('crossovered.budget.lines')
        for axis in self.browse(cr, 1, ids, context):
            if (not axis.active or context.get('unlink_axis') or not axis.is_budget_axis) and axis.column_label in line_obj._columns:
                del line_obj._columns[axis.column_label]
                if axis.field_ids:
                    for field in axis.field_ids:
                        column = '%s_%s' % (axis.column_label, field.id)
                        if column in line_obj._columns:
                            del line_obj._columns[column]
            elif axis.active and axis.is_budget_axis:
                line_obj._columns[axis.column_label] = fields.many2one(axis.model, axis.name,
                                                                       domain=axis.domain and eval(axis.domain) or [],
                                                                       required=axis.required)
                if axis.field_ids:
                    for field in axis.field_ids:
                        column = '%s_%s' % (axis.column_label, field.id)
                        line_obj._columns[column] = fields.related(axis.column_label, field.name,
                                                                   type=field.ttype, relation=field.relation,
                                                                   store={
                                                                       # To store and to avoid the field re-computation
                                                                       'crossovered.budget.lines': (lambda self, cr, uid, ids, context=None: [], None, 10),
                                                                   })
        line_obj._auto_init(cr, context)
        return True
AnalyticAxis()
