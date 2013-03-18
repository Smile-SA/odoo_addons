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
from tools.func import wraps


def indexer(original_method):
    @wraps(original_method)
    def wrapper(self, cr, mode):
        res = original_method(self, cr, mode)
        if isinstance(self, osv.osv_pool):
            analytic_line_obj = self.get('account.analytic.line')
            if analytic_line_obj and hasattr(analytic_line_obj, '_update_index'):
                unicity_fields = analytic_line_obj._get_unicity_fields()
                analytic_line_obj._update_index(cr, unicity_fields)
        return res
    return wrapper


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
            cr.execute('CREATE INDEX account_analytic_line_multi_columns_index '
                       'ON account_analytic_line %s', (tuple(unicity_fields),))

    def _get_unicity_fields(self):
        return [field for field in self._columns
                if self._columns[field]._type not in ('one2many', 'many2many')
                and field not in self._non_unicity_fields]

    def __init__(self, pool, cr):
        super(AnalyticLine, self).__init__(pool, cr)
        if not hasattr(self, '_non_unicity_fields'):
            self._non_unicity_fields = []
        self._non_unicity_fields.extend(['name', 'code', 'ref', 'date', 'create_period_id',
                                         'amount', 'unit_amount', 'amount_currency', 'product_uom_id',
                                         'currency_id', 'move_id', 'user_id', 'active', 'type'])
        setattr(osv.osv_pool, 'init_set', indexer(getattr(osv.osv_pool, 'init_set')))

    def _get_amount_currency(self, cr, uid, ids, name, arg, context=None):
        res = {}
        context = context or {}
        company_obj = self.pool.get('res.company')
        currency_obj = self.pool.get('res.currency')
        if isinstance(ids, (int, long)):
            ids = [ids]
        for analytic_line in self.read(cr, uid, ids, ['amount', 'date', 'currency_id', 'company_id'], context):
            if analytic_line['currency_id'] and analytic_line['company_id']:
                context['date'] = analytic_line['date']
                company_currency_id = company_obj.read(cr, uid, analytic_line['company_id'][0], ['currency_id'], context)['currency_id'][0]
                res[analytic_line['id']] = currency_obj.compute(cr, uid, company_currency_id, analytic_line['currency_id'][0],
                                                                analytic_line['amount'], context=context)
            else:
                res[analytic_line['id']] = analytic_line['amount']
        return res

    def _get_currency_id(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        move_obj = self.pool.get('account.move.line')
        for analytic_line in self.read(cr, uid, ids, ['move_id'], context):
            res[analytic_line['id']] = False
            if analytic_line['move_id']:
                currency_id = move_obj.read(cr, uid, analytic_line['move_id'][0], ['currency_id'], context)['currency_id']
                if currency_id:
                    res[analytic_line['id']] = currency_id[0]
        return res

    def _set_currency_id(self, cr, uid, ids, name, value, arg, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        cr.execute('UPDATE account_analytic_line SET currency_id = %s WHERE id in %s', (value, tuple(ids)))
        return True

    def _get_analytic_line_ids_from_account_moves(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        return self.pool.get('account.analytic.line').search(cr, uid, [('move_id', 'in', ids)], context=context)

    _columns = {
        'currency_id': fields.function(_get_currency_id, fnct_inv=_set_currency_id, method=True, type='many2one', store={
            'account.analytic.line': (lambda self, cr, uid, ids, context=None: ids, ['move_id'], 10),
            'account.move.line': (_get_analytic_line_ids_from_account_moves, ['currency_id'], 10),
        }, relation='res.currency', string='Account currency', help="The related account currency if not equal to the company one.", readonly=True),
        'amount_currency': fields.function(_get_amount_currency, method=True, type='float', string='Amount currency', store={
            'account.analytic.line': (lambda self, cr, uid, ids, context=None: ids, ['amount', 'date', 'account_id', 'move_id'], 20),
        }, help="The amount expressed in the related account currency if not equal to the company one.", readonly=True),
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
            if line.active and line.period_id and getattr(line.period_id.date_start, operator_)(line.create_period_id.date_start) \
                    and line.type == entry_type:
                return False
        return True

    def _check_actual_from_analysis_period(self, cr, uid, ids, context=None):
        return self._check_type_from_analysis_period(cr, uid, ids, 'actual', context)

    def _check_forecast_from_analysis_period(self, cr, uid, ids, context=None):
        return self._check_type_from_analysis_period(cr, uid, ids, 'forecast', context)

    def _check_create_period(self, cr, uid, ids, context=None):
        context = context or {}
        if not context.get('force_analytic_line_update'):
            return super(AnalyticLine, self)._check_create_period(cr, uid, ids, context)
        return True

    _constraints = [
        (_check_actual_from_analysis_period, 'You cannot pass an actual entry in a future period!', ['type', 'period_id']),
        (_check_forecast_from_analysis_period, 'You cannot pass a forecast entry in a past period!', ['type', 'period_id']),
        (_check_create_period, 'You cannot pass/update a journal entry in a closed period!', ['create_period_id']),
    ]

    def _build_unicity_domain(self, line, domain=None):
        domain = list(domain or [])
        for field in self._get_unicity_fields():
            value = isinstance(line[field], tuple) and line[field][0] or line[field]
            domain.append((field, '=', value))
        return domain

    def _deactivate_old_forecast_lines(self, cr, uid, ids, initial_domain=None, context=None):
        if not hasattr(self, '_non_unicity_fields'):
            return True
        line_ids_to_deactivate = []
        context = context or {}
        context['bypass_forecast_lines_deactivation'] = True
        context['force_analytic_line_update'] = True
        if isinstance(ids, (int, long)):
            ids = [ids]
        unicity_fields = self._get_unicity_fields()
        for line in self.read(cr, uid, ids, unicity_fields, {}):
            domain = self._build_unicity_domain(line, initial_domain)
            key_line_ids = self.search(cr, uid, domain, order='create_period_id desc, type asc, id desc', context=context)
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
        if not context_copy.get('bypass_forecast_lines_deactivation'):
            self._deactivate_old_forecast_lines(cr, uid, res_id, context=context_copy)
        return res_id

    def write(self, cr, uid, ids, vals, context=None):
        context = context or {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        if context and not context.get('bypass_forecast_lines_deactivation'):
            context_copy = dict(context or {})
            context_copy['active_test'] = False
            context_copy['forecast_line_to_activate'] = True
            vals = vals or {}
            for field in vals:
                if field not in self._non_unicity_fields:
                    self._deactivate_old_forecast_lines(cr, uid, ids, [('id', 'not in', ids)], context_copy)
                    break
        res = super(AnalyticLine, self).write(cr, uid, ids, vals, context)
        if context and not context.get('bypass_forecast_lines_deactivation'):
            context_copy = dict(context or {})
            context_copy['active_test'] = False
            for field in vals:
                if field not in self._non_unicity_fields or field == 'type':
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


class AnalyticPeriod(osv.osv):
    _inherit = 'account.analytic.period'

    def button_close(self, cr, uid, ids, context=None):
        context_copy = (context or {}).copy()
        context_copy['bypass_forecast_lines_deactivation'] = True
        if isinstance(ids, (int, long)):
            ids = [ids]
        analytic_line_obj = self.pool.get('account.analytic.line')
        analytic_line_ids = analytic_line_obj.search(cr, uid, [
            ('period_id', 'in', ids),
            ('type', '=', 'forecast'),
        ], context={'active_test': True})
        if analytic_line_ids:
            analytic_line_obj.write(cr, uid, analytic_line_ids, {'active': False}, context_copy)
        return super(AnalyticPeriod, self).button_close(cr, uid, ids, context)

AnalyticPeriod()
