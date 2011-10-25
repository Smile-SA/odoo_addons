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

import time

from osv import osv, fields

class AnalyticLine(osv.osv):
    _inherit = 'account.analytic.line'

    def _sort_unicity_fields(self, unicity_fields):
        ordered_list = []
        for field in unicity_fields:
            if self._columns[field].required:
                ordered_list.insert(0, field)
            else:
                ordered_list.append(field)
        return ordered_list

    def _update_index(self, cr, unicity_fields):
        unicity_fields = self._sort_unicity_fields(unicity_fields)
        cr.execute("SELECT count(0) FROM pg_class WHERE relname = 'account_analytic_line_multi_columns_index'")
        exists = cr.fetchone()
        if not exists:
            cr.execute('CREATE INDEX account_analytic_line_multi_columns_index '\
		               'ON account_analytic_line (%s)' % ','.join(unicity_fields))

    def _get_unicity_fields(self):
        return [field for field in self._columns \
            if self._columns[field]._type not in ('one2many', 'many2many') \
            and field not in ('name', 'code', 'ref', 'date', 'create_period_id', \
                              'amount', 'unit_amount', 'amount_currency', 'product_uom_id', \
                              'currency_id', 'move_id', 'user_id', 'active', 'type')]

    def __init__(self, pool, cr):
        super(AnalyticLine, self).__init__(pool, cr)
        self._unicity_fields = self._get_unicity_fields()
        self._update_index(cr, self._unicity_fields)

    _columns = {
        'active': fields.boolean('Active', readonly=True),
        'type': fields.selection([('actual', 'Actual'), ('forecast', 'Forecast')], 'Type', required=True),
    }

    _defaults = {
        'active': True,
        'type': 'actual',
    }

    def _check_type_from_analysis_period(self, cr, uid, ids, entry_type='actual', context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        operator_ = entry_type == 'actual' and '__gt__' or '__lt__'
        for line in self.browse(cr, uid, ids, context):
            if line.active and line.period_id and getattr(line.period_id.date_start, operator_)(time.strftime('%Y-%m-%d')) and line.type == entry_type:
                return False
        return True

    def _check_actual_from_analysis_period(self, cr, uid, ids, context=None):
        return self._check_type_from_analysis_period(cr, uid, ids, 'actual', context)

    def _check_forecast_from_analysis_period(self, cr, uid, ids, context=None):
        return self._check_type_from_analysis_period(cr, uid, ids, 'forecast', context)
    
    _constraints = [
        (_check_actual_from_analysis_period, 'You cannot pass an actual entry in a future period!', ['type', 'period_id']),
        (_check_forecast_from_analysis_period, 'You cannot pass a forecast entry in a past/current period!', ['type', 'period_id']),
    ]

    def _build_unicity_domain(self, line, domain=None):
        domain = list(domain or [])
        for field in self._unicity_fields:
            value = isinstance(line[field], tuple) and line[field][0] or line[field]
            domain.append((field, '=', value))
        return domain

    def _deactivate_old_forecast_lines(self, cr, uid, ids, initial_domain=None, context=None):
        line_ids_to_deactivate = []
        context = context or {}
        context['bypass_forecast_lines_deactivation'] = True
        if isinstance(ids, (int, long)):
            ids = [ids]
        for line in self.read(cr, uid, ids, self._unicity_fields, {}):
            domain = self._build_unicity_domain(line, initial_domain)
            key_line_ids = self.search(cr, uid, domain, order='create_period_id desc, type asc', context=context)
            no_actual_lines = 1
            key_line_id_to_type = dict([(line['id'], line['type']) for line in self.read(cr, uid, key_line_ids, ['type'], context)])
            for index, key_line_id in enumerate(key_line_ids):
                if key_line_id_to_type[key_line_id] == 'actual':
                    no_actual_lines = 0
                if key_line_id_to_type[key_line_id] == 'forecast':
                    if context.get('forecast_line_to_activate') and no_actual_lines:
                        self.write(cr, uid, key_line_id, {'active': True}, context)
                    line_ids_to_deactivate.extend(key_line_ids[index + no_actual_lines:])
                    break
        return self.write(cr, uid, line_ids_to_deactivate, {'active': False}, context)

    def create(self, cr, uid, vals, context=None):
        res_id = super(AnalyticLine, self).create(cr, uid, vals, context)
        context_copy = dict(context or {})
        context_copy['active_test'] = True
        self._deactivate_old_forecast_lines(cr, uid, res_id, context=context_copy)
        return res_id

    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        if context and not context.get('bypass_forecast_lines_deactivation'):
            context_copy = dict(context or {})
            context_copy['active_test'] = False
            context_copy['forecast_line_to_activate'] = True
            vals = vals or {}
            for field in vals:
                if field in self._unicity_fields:
                    self._deactivate_old_forecast_lines(cr, uid, ids, [('id', 'not in', ids)], context_copy)
                    break
        res = super(AnalyticLine, self).write(cr, uid, ids, vals, context)
        if context and not context.get('bypass_forecast_lines_deactivation'):
            context_copy = dict(context or {})
            context_copy['active_test'] = False
            for field in vals:
                if field in self._unicity_fields + ['type']:
                    self._deactivate_old_forecast_lines(cr, uid, ids, context=context_copy)
                    break
        return res

    def unlink(self, cr, uid, ids, context=None):
        context_copy = dict(context or {})
        context_copy['active_test'] = False
        if isinstance(ids, (int, long)):
            ids = [ids]
        self._deactivate_old_forecast_lines(cr, uid, ids, [('id', 'not in', ids)], context_copy)
        return super(AnalyticLine, self).unlink(cr, uid, ids, context)
AnalyticLine()
