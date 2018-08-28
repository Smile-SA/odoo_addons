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

import datetime
import time

from osv import osv, fields, orm
import tools
from tools.func import wraps
from tools.translate import _


def analytic_decorator(original_method):
    @wraps(original_method)
    def wrapper(self, cr, *args, **kwargs):
        res = original_method(self, cr, *args, **kwargs)
        if isinstance(self, osv.osv_pool):
            axis_obj = self.get('account.analytic.axis')
            if axis_obj and hasattr(axis_obj, '_update_analytic_line_columns'):
                axis_obj._update_analytic_line_columns(cr)
        return res
    return wrapper


class AnalyticAxis(osv.osv):
    _name = 'account.analytic.axis'
    _description = 'Analytic Axis'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'column_label': fields.char('Analytic line column label', size=55, required=True),
        'active': fields.boolean('Active'),
        'model_id': fields.many2one('ir.model', 'Object', domain=[('osv_memory', '=', False)], required=True, ondelete='restrict'),
        'model': fields.related('model_id', 'model', type='char', string="Model"),
        'domain': fields.char("Domain", size=256, required=True),
        'required': fields.boolean('Required'),
        'field_ids': fields.many2many('ir.model.fields', 'account_analytic_axis_field_rel', 'axis_id', 'field_id', 'Fields to historicize'),
        'is_unicity_field': fields.boolean('Unicity field', help="Useful only if the module smile_analytic_forecasting is installed"),
        'ondelete': fields.selection([('cascade', 'CASCADE'), ('set null', 'SET NULL'), ('restrict', 'RESTRICT')], 'On delete', required=True),
    }

    _defaults = {
        'active': True,
        'domain': '[]',
        'is_unicity_field': True,
        'ondelete': 'restrict',
    }

    def _check_column_label(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for axis in self.read(cr, uid, ids, ['column_label'], context):
            for character in axis['column_label']:
                if character not in 'abcdefghijklmnopqrstuvwxyz0123456789_':
                    return False
        return True

    _constraints = [
        (_check_column_label, 'Analytic line column label is only composed of alphanumeric characters and underscore', ['column_label']),
    ]

    def _update_analytic_line_columns(self, cr, ids=None, context=None):
        context = context or {}

        if isinstance(ids, (int, long)):
            ids = [ids]
        if not ids:
            ids = self.search(cr, 1, [], context={'active_test': False})

        line_obj = self.pool.get('account.analytic.line')
        non_unicity_fields = line_obj._non_unicity_fields[:]
        for axis in self.browse(cr, 1, ids, context):
            if (not axis.active or context.get('unlink_axis')) and axis.column_label in line_obj._columns:
                del line_obj._columns[axis.column_label]
                if axis.field_ids:
                    for field in axis.field_ids:
                        column = '%s_%s' % (axis.column_label, field.id)
                        if column in line_obj._columns:
                            del line_obj._columns[column]
            elif axis.active:
                # To be compatible with smile_analytic_forecasting
                if hasattr(line_obj, '_non_unicity_fields'):
                    if axis.is_unicity_field and axis.column_label in line_obj._non_unicity_fields:
                        line_obj._non_unicity_fields.remove(axis.column_label)
                    elif not axis.is_unicity_field and axis.column_label not in line_obj._non_unicity_fields:
                        line_obj._non_unicity_fields.append(axis.column_label)
                ###
                line_obj._columns[axis.column_label] = fields.many2one(axis.model, axis.name,
                                                                       domain=axis.domain and eval(axis.domain) or [],
                                                                       required=axis.required, ondelete=axis.ondelete)
                if axis.field_ids:
                    for field in axis.field_ids:
                        column = '%s_%s' % (axis.column_label, field.id)
                        line_obj._columns[column] = fields.related(axis.column_label,
                                                                   field.name, type=field.ttype,
                                                                   relation=field.relation, store={
                                                                       # To store and to avoid the field re-computation
                                                                       'account.analytic.line': (lambda self, cr, uid, ids,
                                                                                                 context=None: [], None, 10),
                                                                   })
        line_obj._auto_init(cr, context)

        # To be compatible with smile_analytic_forecasting
        if hasattr(line_obj, '_non_unicity_fields'):
            if line_obj._non_unicity_fields != non_unicity_fields:
                cr.execute("SELECT count(0) FROM pg_class WHERE relname = 'account_analytic_line_multi_columns_index'")
                exists = cr.fetchone()
                if exists[0]:
                    cr.execute('DROP INDEX account_analytic_line_multi_columns_index')
                cr.execute('CREATE INDEX account_analytic_line_multi_columns_index '
                           'ON account_analytic_line (%s)' % ', '.join(line_obj._get_unicity_fields()))
        ###
        return True

    def __init__(self, pool, cr):
        super(AnalyticAxis, self).__init__(pool, cr)
        setattr(osv.osv_pool, 'init_set', analytic_decorator(getattr(osv.osv_pool, 'init_set')))

    def create(self, cr, uid, vals, context=None):
        res_id = super(AnalyticAxis, self).create(cr, uid, vals, context)
        self._update_analytic_line_columns(cr, res_id, context)
        return res_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(AnalyticAxis, self).write(cr, uid, ids, vals, context)
        self._update_analytic_line_columns(cr, ids, context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        context = context or {}
        context['unlink_axis'] = True
        self._update_analytic_line_columns(cr, ids, context)
        return super(AnalyticAxis, self).unlink(cr, uid, ids, context)
AnalyticAxis()


def concatenate_with_comma(string1, string2):
    if not string1 or not string2:
        return string1 or string2 or ''
    else:
        return ', '.join([unicode(string1), unicode(string2)])


def name_get(obj, cr, uid, res_id, context=None):
    res_name = obj.name_get(cr, uid, res_id, context)
    return res_name and res_name[0] or (0, _('Unknown'))


class AnalyticDistribution(osv.osv):
    _name = 'account.analytic.distribution'
    _description = 'Analytic Distribution'
    _order = 'priority asc'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'active': fields.boolean('Active'),
        'priority': fields.integer('Priority', required=True),
        'axis_src_id': fields.many2one('account.analytic.axis', 'Source Axis', required=True, ondelete='cascade'),
        'axis_dest_id': fields.many2one('account.analytic.axis', 'Destination Axis', required=True, ondelete='cascade'),
        'period_ids': fields.one2many('account.analytic.distribution.period', 'distribution_id', 'Application Periods'),
        'company_id': fields.many2one('res.company', 'Company'),
        'computation_mode': fields.selection([
            ('static', 'Static'),
            ('dynamic', 'Dynamic'),
        ], 'Computation Mode', required=True),
        'python_code': fields.text('Python code', help=""),
        'journal_ids': fields.many2many('account.analytic.journal', 'account_analytic_distribution_journal_rel',
                                        'distribution_id', 'journal_id', 'Journals'),
        'distribution_type': fields.selection([
            ('global', 'Global'),
            ('specific', 'Specific'),
        ], 'Distribution Type', required=True),
        'axis_src_item_ids': fields.one2many('account.analytic.distribution.axis_src_item', 'distribution_id', 'Items of Source Axis'),
    }

    _defaults = {
        'active': True,
        'priority': 15,
        'computation_mode': 'static',
        'distribution_type': 'specific',
        'python_code': """# You can use the following variables
#    - objects
#    - self
#    - cr
#    - uid
#    - ids
#    - date
# You must return a dictionary, assign: result = {axis_src_item_id: {axis_dest_item_id: {'rate': rate, 'audit': 'dist%s' % distribution_id}}}
""",
    }

    @tools.cache(skiparg=3)
    def _get_distribution_destinations(self, cr, uid):
        distribution_ids = self.search(cr, uid, [], context={'active_test': True})
        return dict([(distrib.id, distrib.axis_dest_id.model) for distrib in self.browse(cr, uid, distribution_ids)
                     if distrib.computation_mode == 'static'])

    def create(self, cr, uid, vals, context=None):
        distribution_id = super(AnalyticDistribution, self).create(cr, uid, vals, context)
        self._get_distribution_destinations.clear_cache(cr.dbname)
        return distribution_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(AnalyticDistribution, self).write(cr, uid, ids, vals, context)
        self._get_distribution_destinations.clear_cache(cr.dbname)
        return res

    def unlink(self, cr, uid, ids, context=None):
        res = super(AnalyticDistribution, self).unlink(cr, uid, ids, context)
        self._get_distribution_destinations.clear_cache(cr.dbname)
        return res

    def _get_destinations_for_distribution(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        distribution_destinations = self._get_distribution_destinations(cr, uid)
        return [distribution_destinations[distribution_id] for distribution_id in ids
                if distribution_id in distribution_destinations]  # filter inactive distributions

    def _get_distribution_period_ids(self, cr, uid, distribution_id, date, context=None):
        period_domain = [
            ('distribution_id', '=', distribution_id),
            '|', ('date_start', '=', False), ('date_start', '<=', date),
            '|', ('date_stop', '=', False), ('date_stop', '>=', date),
        ]
        return self.pool.get('account.analytic.distribution.period').search(cr, uid, period_domain, limit=1, context=context)

    def _get_specific_static_distribution(self, cr, uid, distribution_id, date, res_ids, context=None):
        res = {}
        period_ids = self._get_distribution_period_ids(cr, uid, distribution_id, date)
        key_obj = self.pool.get('account.analytic.distribution.key')
        key_domain = [('period_id', 'in', period_ids)]
        if res_ids:
            key_domain.append(('axis_src_item_id', 'in', res_ids))
        key_ids = key_obj.search(cr, uid, key_domain, context=context)
        for key in key_obj.read(cr, uid, key_ids, ['axis_src_item_id', 'axis_dest_item_id', 'rate'], context):
            res.setdefault(key['axis_src_item_id'], {}).update({key['axis_dest_item_id']: {
                'rate': key['rate'],
                'audit': 'dist%s_key%s' % (distribution_id, key['id']),
            }})
        return res

    def _get_global_static_distribution(self, cr, uid, distribution_id, date, res_ids, context=None):
        res = {}
        period_ids = self._get_distribution_period_ids(cr, uid, distribution_id, date)
        key_obj = self.pool.get('account.analytic.distribution.key')
        key_ids = key_obj.search(cr, uid, [('period_id', 'in', period_ids)])
        keys = key_obj.read(cr, uid, key_ids, ['axis_dest_item_id', 'rate'], context)
        axis_src_item_obj = self.pool.get('account.analytic.distribution.axis_src_item')
        axis_src_item_ids = axis_src_item_obj.search(cr, uid, [('distribution_id', '=', distribution_id)], context=context)
        axis_src_items = axis_src_item_obj.read(cr, uid, axis_src_item_ids, ['res_id'], context)
        for axis_src_item in axis_src_items:
            for key in keys:
                res.setdefault(axis_src_item['res_id'], {}).update({key['axis_dest_item_id']: {
                    'rate': key['rate'],
                    'audit': 'dist%s_key%s' % (distribution_id, key['id']),
                }})
        return res

    def _get_dynamic_distribution(self, cr, uid, distribution_id, date, res_ids, context=None):
        distribution = self.browse(cr, uid, distribution_id, context)
        model_obj = self.pool.get(distribution.axis_src_id.model)
        res_ids = res_ids or model_obj.search(cr, uid, [], context=context)
        localdict = {
            'objects': model_obj.browse(cr, uid, res_ids),
            'self': model_obj,
            'cr': cr,
            'uid': uid,
            'ids': res_ids,
            'date': date,
            'datetime': datetime,
            'distribution_id': distribution.id,
            'audit': 'dist%s' % distribution.id,
        }
        exec distribution.python_code in localdict
        return localdict.get('result', {})

    def get_distribution(self, cr, uid, distribution_id, date=None, res_ids=None, context=None):
        assert distribution_id and isinstance(distribution_id, (int, long)), 'distribution_id must be an integer'
        assert res_ids is None or isinstance(res_ids, (list, tuple)), 'res_ids must be a list or a tuple'
        date = date or time.strftime('%Y-%m-%d')
        distribution = self.read(cr, uid, distribution_id, ['computation_mode', 'distribution_type'], context)
        distribution_type = distribution['computation_mode']
        if distribution['computation_mode'] == 'static':
            distribution_type = '%s_%s' % (distribution['distribution_type'], distribution['computation_mode'])
        return getattr(self, '_get_%s_distribution' % distribution_type)(cr, uid, distribution['id'], date, res_ids, context)

    def apply_distribution_keys(self, cr, uid, distribution_id, line_vals, context=None):
        assert distribution_id and isinstance(distribution_id, (int, long)), 'distribution_id must be an integer'
        assert line_vals and isinstance(line_vals, dict), 'line_vals must be a dictionary'
        res = []
        distribution = self.browse(cr, uid, distribution_id, context)
        column_src = distribution.axis_src_id.column_label
        column_dest = distribution.axis_dest_id.column_label
        res_ids = line_vals.get(column_src) and [line_vals[column_src]] or []
        distribution_keys = self.get_distribution(cr, uid, distribution_id, line_vals.get('date'), res_ids)
        axis_src_item_id = line_vals.get(column_src)
        if not distribution_keys or not distribution_keys.get(axis_src_item_id):
            res = [line_vals]
        else:
            for axis_dest_item_id in distribution_keys[axis_src_item_id]:
                rate = distribution_keys[axis_src_item_id][axis_dest_item_id]['rate'] / 100.0
                audit = distribution_keys[axis_src_item_id][axis_dest_item_id].get('audit')
                new_vals = dict(line_vals)
                new_vals.update({
                    column_dest: axis_dest_item_id,
                    'amount': line_vals.get('amount', 0.0) * rate,
                    'unit_amount': line_vals.get('unit_amount', 0.0) * rate,
                    'amount_currency': line_vals.get('amount_currency', 0.0) * rate,
                    'audit': concatenate_with_comma(line_vals.get('audit'), audit),
                })
                res.append(new_vals)
        return res
AnalyticDistribution()


class AnalyticDistributionItem(osv.osv):
    _name = 'account.analytic.distribution.axis_src_item'
    _description = 'Analytic Distribution Source Axis Item'
    _rec_name = 'res_name'

    def _get_names(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        for item in self.read(cr, uid, ids, ['res_id', 'res_model']):  # Do not pass context to avoid to receive a many2one instead of integer
            item_name = self.pool.get(item['res_model']).name_get(cr, uid, [item['res_id']], context)
            res[item['id']] = item_name and item_name[0][1] or ''
        return res

    _columns = {
        'distribution_id': fields.many2one('account.analytic.distribution', 'Distribution', required=True, ondelete='cascade'),
        'res_model': fields.related('distribution_id', 'axis_src_id', 'model_id', 'model', type='char', size=64,
                                    string='Resource Model', store=True, readonly=True),
        'res_id': fields.integer('Resource Identifier', required=True),
        'res_name': fields.function(_get_names, method=True, type='char', string='Resource Name'),
    }

    def read(self, cr, uid, ids, allfields=None, context=None, load='_classic_read'):
        res = super(AnalyticDistributionItem, self).read(cr, uid, ids, allfields, context, load)
        context = context or {}
        if context.get('axis_src_id'):
            axis = self.pool.get('account.analytic.axis').browse(cr, uid, context['axis_src_id'], context)
            if not allfields or 'res_id' in allfields:
                model_obj = self.pool.get(axis.model)
                if isinstance(res, dict):
                    res['res_id'] = name_get(model_obj, cr, uid, res['res_id'], context)
                elif isinstance(res, list):
                    for index in range(len(res)):
                        res[index]['res_id'] = name_get(model_obj, cr, uid, res[index]['res_id'], context)
        return res

    def fields_get(self, cr, uid, allfields=None, context=None):
        res = super(AnalyticDistributionItem, self).fields_get(cr, uid, allfields, context)
        context = context or {}
        if context.get('axis_src_id'):
            axis = self.pool.get('account.analytic.axis').browse(cr, uid, context['axis_src_id'], context)
            if not allfields or 'res_id' in allfields:
                res['res_id'].update({
                    'string': axis.model_id.name,
                    'type': 'many2one',
                    'relation': axis.model,
                    'domain': axis.domain and eval(axis.domain),
                })
        return res
AnalyticDistributionItem()


class AnalyticDistributionPeriod(osv.osv):
    _name = 'account.analytic.distribution.period'
    _description = 'Analytic Distribution Application Period'
    _rec_name = 'distribution_id'

    _columns = {
        'distribution_id': fields.many2one('account.analytic.distribution', 'Distribution', required=True, ondelete='cascade'),
        'date_start': fields.date('Start Date'),
        'date_stop': fields.date('End Date'),
        'key_ids': fields.one2many('account.analytic.distribution.key', 'period_id', 'Keys'),
        'company_id': fields.related('distribution_id', 'company_id', type='many2one', relation='res.company', string='Company', readonly=True),
    }

    def _check_periods_overlap(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for period in self.browse(cr, uid, ids, context):
            domain = [('id', '<>', period.id), ('distribution_id', '=', period.distribution_id.id)]
            if period.date_start:
                domain += ['|', ('date_stop', '>=', period.date_start), ('date_stop', '=', False)]
            if period.date_stop:
                domain += ['|', ('date_start', '<=', period.date_stop), ('date_start', '=', False)]
            if self.search(cr, uid, domain, context={'active_test': True}):
                return False
        return True

    _constraints = [
        (_check_periods_overlap, 'Some application periods overlap!', ['date_start', 'date_stop']),
    ]
AnalyticDistributionPeriod()


class AnalyticDistributionKey(osv.osv):
    _name = 'account.analytic.distribution.key'
    _description = 'Analytic Distribution Key'
    _rec_name = 'period_id'

    def _get_items(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        for key in self.read(cr, uid, ids, ['axis_src_item_id', 'axis_src_model', 'axis_dest_item_id', 'axis_dest_model']):
            # Do not pass context to avoid to receive many2one instead of integer
            axis_src_item_name = self.pool.get(key['axis_src_model']).name_get(cr, uid, [key['axis_src_item_id']], context)
            axis_dest_item_name = self.pool.get(key['axis_dest_model']).name_get(cr, uid, [key['axis_dest_item_id']], context)
            res[key['id']] = {
                'axis_src_item_name': axis_src_item_name and axis_src_item_name[0][1] or '',
                'axis_dest_item_name': axis_dest_item_name and axis_dest_item_name[0][1] or '',
            }
        return res

    _columns = {
        'period_id': fields.many2one('account.analytic.distribution.period', 'Distribution Application Period', required=True, ondelete='cascade'),
        'axis_src_item_id': fields.integer('Item of Source Axis', required=False),
        'axis_src_model': fields.related('period_id', 'distribution_id', 'axis_src_id', 'model', string="Model of Source Axis", readonly=True),
        'axis_src_item_name': fields.function(_get_items, method=True, type='char', string='Item of Source Axis', multi='distribution_key'),
        'axis_dest_item_id': fields.integer('Item of Destination Axis', required=True),
        'axis_dest_model': fields.related('period_id', 'distribution_id', 'axis_dest_id', 'model', string="Model of Destination Axis", readonly=True),
        'axis_dest_item_name': fields.function(_get_items, method=True, type='char', string='Item of Destination Axis', multi='distribution_key'),
        'rate': fields.float('Rate (%)', required=True),
        'company_id': fields.related('period_id', 'distribution_id', 'company_id', type='many2one', relation='res.company', string='Company',
                                     readonly=True),
        'active': fields.boolean('Active', readonly=True),
        'date_start': fields.related('period_id', 'date_start', type='date', string='Start Date', readonly=True, store=True),
        'date_stop': fields.related('period_id', 'date_stop', type='date', string='End Date', readonly=True, store=True),
    }

    _defaults = {
        'active': True,
        'date_start': time.strftime('%Y-%m-%d'),
    }

    def read(self, cr, uid, ids, allfields=None, context=None, load='_classic_read'):
        res = super(AnalyticDistributionKey, self).read(cr, uid, ids, allfields, context, load)
        context = context or {}
        if context.get('distribution_id'):
            distribution = self.pool.get('account.analytic.distribution').browse(cr, uid, context['distribution_id'], context)
            for field in ('axis_src_item_id', 'axis_dest_item_id'):
                if not allfields or field in allfields:
                    model = getattr(distribution, field.replace('_item', '')).model
                    model_obj = self.pool.get(model)
                    if isinstance(res, dict):
                        res['res_id'] = name_get(model_obj, cr, uid, res['res_id'], context)
                    elif isinstance(res, list):
                        for index in range(len(res)):
                            res[index]['res_id'] = name_get(model_obj, cr, uid, res[index]['res_id'], context)
        return res

    def fields_get(self, cr, uid, allfields=None, context=None):
        res = super(AnalyticDistributionKey, self).fields_get(cr, uid, allfields, context)
        context = context or {}
        if context.get('distribution_id'):
            distribution = self.pool.get('account.analytic.distribution').browse(cr, uid, context['distribution_id'], context)
            for field in ('axis_src_item_id', 'axis_dest_item_id'):
                if not allfields or field in allfields:
                    axis = getattr(distribution, field.replace('_item', ''))
                    res[field].update({
                        'string': axis.model_id.name,
                        'type': 'many2one',
                        'relation': axis.model,
                        'domain': axis.domain and eval(axis.domain),
                    })
        return res

    def _deactivate_old_key(self, cr, uid, key_id, context=None):
        context = context or {}
        context['distribution_key_deactivation_in_progress'] = True
        key = self.browse(cr, uid, key_id)  # Do not pass context in order to have integer type fields
        domain = [
            ('id', '!=', key.id),
            ('period_id', '=', key.period_id.id),
            ('axis_src_item_id', '=', key.axis_src_item_id),
            ('axis_dest_item_id', '=', key.axis_dest_item_id),
        ]
        key_ids_to_deactivate = self.search(cr, uid, domain, context={'active_test': True})
        if not key.rate:
            key.write({'active': False}, context)
        if key_ids_to_deactivate:
            self.write(cr, uid, key_ids_to_deactivate, {'active': False, 'date_stop': time.strftime('%Y-%m-%d')}, context)
        return True

    def create(self, cr, uid, vals, context=None):
        new_key_id = super(AnalyticDistributionKey, self).create(cr, uid, vals, context)
        self._deactivate_old_key(cr, uid, new_key_id, context)
        return new_key_id

    def write(self, cr, uid, ids, vals, context=None):
        context = context or {}
        if not context.get('distribution_key_deactivation_in_progress'):
            if isinstance(ids, (int, long)):
                ids = [ids]
            vals.update({'date_start': time.strftime('%Y-%m-%d'), 'date_stop': False, 'active': True})
            for key_id in ids:
                new_key_id = self.copy(cr, uid, key_id, vals, context)
                self._deactivate_old_key(cr, uid, new_key_id, context)
            return True
        else:
            return super(AnalyticDistributionKey, self).write(cr, uid, ids, vals, context)

    def _reactivate_old_keys(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        old_key_ids = []
        for key in self.browse(cr, uid, ids):  # Do not pass context in order to have integer type fields
            domain = [
                ('id', '!=', key.id),
                ('period_id', '=', key.period_id.id),
                ('axis_src_item_id', '=', key.axis_src_item_id),
                ('axis_dest_item_id', '=', key.axis_dest_item_id),
            ]
            old_key_ids.extend(self.search(cr, uid, domain, limit=1, order='date_stop desc', context={'active_test': True}))
        if old_key_ids:
            self.write(cr, uid, old_key_ids, {'active': True, 'date_stop': False}, context)
        return True

    def unlink(self, cr, uid, ids, context=None):
        self._reactivate_old_keys(cr, uid, ids, context)
        return super(AnalyticDistributionKey, self).unlink(cr, uid, ids, context)
AnalyticDistributionKey()


class AnalyticJournal(osv.osv):
    _inherit = 'account.analytic.journal'

    _columns = {
        'distribution_ids': fields.many2many('account.analytic.distribution', 'account_analytic_distribution_journal_rel',
                                             'journal_id', 'distribution_id', 'Distributions'),
    }
AnalyticJournal()


class AnalyticLine(osv.osv):
    _inherit = 'account.analytic.line'

    def __init__(self, pool, cr):
        super(AnalyticLine, self).__init__(pool, cr)
        if 'account_id' in self._columns:
            self._columns['account_id'].required = False
        if not hasattr(self, '_non_unicity_fields'):
            self._non_unicity_fields = []
        self._non_unicity_fields.extend(['audit', 'audit_ref'])

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

    _columns = {
        'amount_currency': fields.function(_get_amount_currency, method=True, type='float', string='Amount currency', store={
            'account.analytic.line': (lambda self, cr, uid, ids, context=None: ids, ['amount', 'date', 'account_id', 'move_id'], 10),
        }, help="The amount expressed in the related account currency if not equal to the company one.", readonly=True),
        'audit': fields.text('Audit', readonly=True),
        'audit_ref': fields.char('Audit Ref', size=12, readonly=True),
    }

    def _distribute(self, cr, uid, vals, context=None):
        res = [vals]
        if vals.get('journal_id'):
            distribution_ids = self.pool.get('account.analytic.journal').read(cr, uid, vals['journal_id'], ['distribution_ids'],
                                                                              context)['distribution_ids']
            distribution_obj = self.pool.get('account.analytic.distribution')
            circular_count = 0
            circular_limit = len(distribution_ids)
            while distribution_ids and circular_count <= circular_limit:
                circular_count += 1
                for distrib in distribution_obj.browse(cr, uid, distribution_ids, context):
                    res_with_src = [line_vals for line_vals in res if line_vals.get(distrib.axis_src_id.column_label)]
                    res_with_src_and_without_dest = [(index, line_vals) for index, line_vals in enumerate(res)
                                                     if line_vals.get(distrib.axis_src_id.column_label)
                                                     and not line_vals.get(distrib.axis_dest_id.column_label)]
                    if res_with_src and not res_with_src_and_without_dest:
                        distribution_ids.remove(distrib.id)
                    elif res_with_src_and_without_dest:
                        index_to_remove = []
                        for index, line_vals in res_with_src_and_without_dest:
                            index_to_remove.append(index)
                            res.extend(distribution_obj.apply_distribution_keys(cr, uid, distrib.id, line_vals, context))
                        for index in sorted(index_to_remove, reverse=True):
                            del res[index]
                    elif distrib.axis_dest_id.model not in distribution_obj._get_destinations_for_distribution(cr, uid, distribution_ids, context):
                        distribution_ids.remove(distrib.id)
        return res

    def create(self, cr, uid, vals, context=None):
        res_ids = []
        if not vals.get('audit_ref'):
            vals['audit_ref'] = self.pool.get('ir.sequence').get(cr, uid, 'account.analytic.line.audit')
        for new_vals in self._distribute(cr, 1, vals, context):
            res_ids.append(super(AnalyticLine, self).create(cr, uid, new_vals, context))
        return res_ids[0]
AnalyticLine()


def _is_distribution_destination(self, cr, uid):
    if self.pool.get('account.analytic.distribution') \
            and self._name in self.pool.get('account.analytic.distribution')._get_distribution_destinations(cr, 1).keys():
        return True
    return False


def analytic_multiaxis_decorator(original_method):
    def check_deactivation(self, cr, uid, ids, *args, **kwargs):
        # Check if resource is deactivated or deleted
        method_name = original_method.__name__
        if _is_distribution_destination(self, cr, uid):
            exception = False
            if isinstance(ids, (int, long)):
                ids = [ids]
            if method_name == 'unlink':
                key_ids = self.pool.get('account.analytic.distribution.key').search(cr, uid, [('axis_dest_item_id', 'in', ids)],
                                                                                    context={'active_test': True})
                if key_ids:
                    exception = True
            elif method_name == 'write':
                if 'active' in args[0] and not args[0]['active']:
                    for resource in self.read(cr, uid, ids, ['active']):
                        if resource['active']:
                            exception = True
                            break
            if exception:
                methods = {'write': _('modify'), 'unlink': _('delete')}
                raise osv.except_osv(_('Error'), _('You cannot %s this resource before reviewing associated analytic distributions!')
                                     % methods[method_name])
        # Execute original method
        return original_method(self, cr, uid, ids, *args, **kwargs)
    return check_deactivation

# TODO: Deals with fields.function.get and fields.function.set
for orm_method in [orm.orm.write, orm.orm.unlink]:
    if hasattr(orm_method.im_class, orm_method.__name__):
        setattr(orm_method.im_class, orm_method.__name__, analytic_multiaxis_decorator(getattr(orm_method.im_class, orm_method.__name__)))
