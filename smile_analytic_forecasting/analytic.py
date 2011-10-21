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

    def __init__(self, pool, cr):
        super(AnalyticLine, self).__init__(pool, cr)
        self._unicity_fields = [field for field in self._columns \
            if self._columns[field]._type not in ('one2many', 'many2many') \
            and field not in ('name', 'code', 'ref', 'date', 'create_period_id', \
                              'amount', 'unit_amount', 'amount_currency', \
                              'currency_id', 'move_id')]

    def _get_period_id(self, cr, uid, ids, name, arg, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = {}.fromkeys(ids, False)
        period_obj = self.pool.get('account.analytic.period')
        for line in self.read(cr, uid, ids, ['date'], context):
            res[line['id']] = period_obj.get_period_id_from_date(cr, uid, line['date'], context)
        return res

    _columns = {
        'active': fields.boolean('Active'),
        'type': fields.selection([('actual', 'Actual'), ('forecast', 'Forecast')], 'Type', required=True),
        'create_period_id': fields.many2one('account.analytic.period', 'Create Period', domain=[('state', '!=', 'done')]),
    }

    def _get_default_period_id(self, cr, uid, context=None):
        return self.pool.get('account.analytic.period').get_period_id_from_date(cr, uid, context=context)

    _defaults = {
        'active': True,
        'type': 'actual',
        'create_period_id': _get_default_period_id,
    }

    def _check_create_period(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for line in self.browse(cr, uid, ids, context):
            if line.create_period_id.state == 'done':
                return False
        return True

    def _check_type_from_analysis_period(self, cr, uid, ids, entry_type='actual', context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        operator_ = entry_type == 'actual' and '__gt__' or '__lt__'
        for line in self.browse(cr, uid, ids, context):
            if line.period_id and getattr(line.period_id.date_start, operator_)(time.strftime('%Y-%m-%d')) and line.type == entry_type:
                return False
        return True

    def _check_actual_from_analysis_period(self, cr, uid, ids, context=None):
        return self._check_type_from_analysis_period(cr, uid, ids, 'actual', context)

    def _check_forecast_from_analysis_period(self, cr, uid, ids, context=None):
        return self._check_type_from_analysis_period(cr, uid, ids, 'forecast', context)
    
    _constraints = [
        (_check_create_period, 'You cannot pass/update a journal entry in a period closed!', ['create_period_id']),
        (_check_actual_from_analysis_period, 'You cannot pass an actual entry in a future period!', ['type', 'create_period_id']),
        (_check_forecast_from_analysis_period, 'You cannot pass a forecast entry in a past period!', ['type', 'create_period_id']),
    ]

    def _deactivate_old_forecast_lines(self, cr, uid, ids, context=None):
        line_ids_to_deactivate = []
        context = context or {}
        context['active_test'] = not context.has_key('ids_to_exclude')
        unicity_fields = self._unicity_fields
        if isinstance(ids, (int, long)):
            ids = [ids]
        for line in self.read(cr, uid, ids, unicity_fields, {}):
            domain = []
            if context.get('ids_to_exclude'):
                domain.append(('id', 'not in', context['ids_to_exclude']))
            for field in unicity_fields:
                value = isinstance(line[field], tuple) and line[field][0] or line[field]
                domain.append((field, '=', value))
            key_line_ids = self.search(cr, uid, domain, order='create_period_id desc, type asc', context=context)
            no_actual_lines = 1
            for index, key_line in enumerate(self.read(cr, uid, key_line_ids, ['type'], context)):
                if key_line['type'] == 'actual':
                    no_actual_lines = 0
                if key_line['type'] == 'forecast':
                    line_ids_to_deactivate.extend(key_line_ids[index + no_actual_lines:])
                    break
        return self.write(cr, uid, line_ids_to_deactivate, {'active': False}, context)

    def create(self, cr, uid, vals, context=None):
        res_id = super(AnalyticLine, self).create(cr, uid, vals, context)
        self._deactivate_old_forecast_lines(cr, uid, res_id, context)
        return res_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(AnalyticLine, self).write(cr, uid, ids, vals, context)
        unicity_fields = self._unicity_fields + ['period_id', 'type']
        for field in vals:
            if field in unicity_fields:
                self._deactivate_old_forecast_lines(cr, uid, ids, context)
                break
        return res

    def unlink(self, cr, uid, ids, context=None):
        context = context or {}
        context['ids_to_exclude'] = isinstance(ids, (int, long)) and [ids] or ids
        res = super(AnalyticLine, self).unlink(cr, uid, ids, context)
        self._deactivate_old_forecast_lines(cr, uid, ids, context)
        return res
AnalyticLine()
