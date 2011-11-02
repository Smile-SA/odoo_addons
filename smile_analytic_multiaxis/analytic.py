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

from osv import osv, fields

def analytic_decorator(original_method):
    def update_analytic_line(self, cr, *args, **kwargs):
        res = original_method(self, cr, *args, **kwargs)        
        if isinstance(self, osv.osv_pool) and self.get('account.analytic.axis') \
        and hasattr(self.get('account.analytic.axis'), '_update_analytic_line_columns'):
            self.get('account.analytic.axis')._update_analytic_line_columns(cr)
        return res
    return update_analytic_line

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
    }
    
    _defaults = {
        'active': True,
        'domain': '[]',
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
        for axis in self.browse(cr, 1, ids, context):
            if (not axis.active or context.get('unlink_axis')) and axis.column_label in line_obj._columns:
                del line_obj._columns[axis.column_label]
                if axis.field_ids:
                    for field in axis.field_ids:
                        column = '%s_%s' % (axis.column_label, field.id)
                        if column in line_obj._columns:
                            del line_obj._columns[column]
            elif axis.active:
                line_obj._columns[axis.column_label] = fields.many2one(axis.model, axis.name, \
                    domain=axis.domain and eval(axis.domain) or [], required=axis.required)
                if axis.field_ids:
                    for field in axis.field_ids:
                        column = '%s_%s' % (axis.column_label, field.id)
                        line_obj._columns[column] = fields.related(axis.column_label, field.name, \
                            type=field.ttype, relation=field.relation, store={
                                # To store and to avoid the field re-computation
                                'account.analytic.line': (lambda self, cr, uid, ids, context=None: [], None, 10),
                            })
        line_obj._auto_init(cr, context)
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

class AnalyticDistribution(osv.osv):
    _name = 'account.analytic.distribution'
    _description = 'Analytic Distribution'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'active': fields.boolean('Active'),
        'axis_src_id': fields.many2one('account.analytic.axis', 'Source Axis', required=True, ondelete='cascade'),
        'axis_dest_id': fields.many2one('account.analytic.axis', 'Destination Axis', required=True, ondelete='cascade'),
        'period_ids': fields.one2many('account.analytic.distribution.period', 'distribution_id', 'Application Periods'),
        'company_id': fields.many2one('res.company', 'Company'),
        'type': fields.selection([
            ('static', 'Static'),
            ('dynamic', 'Dynamic'),
        ], 'Type', required=True),
        'python_code': fields.text('Python code', help=""),
        'journal_ids': fields.many2many('account.analytic.journal', 'analytic_distribution_journal_rel', 'distribution_id', 'journal_id', 'Journals'),
    }

    _defaults = {
        'active': True,
        'type': 'static',
        'python_code': """# You can use the following variables
#    - objects
#    - self
#    - cr
#    - uid
#    - ids
#    - date
# You must return a dictionary, assign: result = {axis_src_item_id: {axis_dest_item_id: {'rate': rate, 'key_id': key_id}}}
""",
    }

    def _get_static_distribution(self, cr, uid, distribution_id, date, res_ids, context):
        res = {}
        period_obj = self.pool.get('account.analytic.distribution.period')
        period_domain = [
            ('distribution_id', '=', distribution_id),
            '|', ('date_start', '=', False), ('date_start', '<=', date),
            '|', ('date_stop', '=', False), ('date_stop', '>=', date),
        ]
        period_ids = period_obj.search(cr, uid, period_domain, limit=1, context=context)
        key_obj = self.pool.get('account.analytic.distribution.key')
        key_domain = [('period_id', 'in', period_ids)]
        if res_ids:
            key_domain.append(('axis_src_item_id', 'in', res_ids))
        key_ids = key_obj.search(cr, uid, key_domain, context=context)
        for key in key_obj.browse(cr, uid, key_ids, context):
            res.setdefault(key['axis_src_item_id'], {}).update({key['axis_dest_item_id']: {'rate': key['rate'], 'key_id': key['id']}})
        return res

    def _get_dynamic_distribution(self, cr, uid, distribution_id, date, res_ids, context):
        distribution = self.browse(cr, uid, distribution_id, context)
        model_obj = self.pool.get(distribution.axis_src_id.model)
        res_ids = res_ids or model_obj.search(cr, uid, [], context=context)
        localdict = {
            'objects': model_obj.browse(cr, uid, res_ids, context),
            'self': model_obj,
            'cr': cr,
            'uid': uid,
            'ids': res_ids,
            'date': date,
            'datetime': datetime,
        }
        exec distribution.python_code in localdict
        return localdict.get('result', {})

    def get_distribution(self, cr, uid, distribution_id, date=None, res_ids=None, context=None):
        assert isinstance(distribution_id, (int, long)), 'distribution_id must be an integer'
        assert res_ids is None or isinstance(res_ids, (list, tuple)), 'res_ids must be a list or a tuple'
        date = date or time.strftime('%Y-%m-%d')
        context = dict(context or {})
        context['active_test'] = True
        if context.has_key('distribution_id'):
            del context['distribution_id']
        distribution = self.read(cr, uid, distribution_id, ['type'], context)
        return getattr(self, '_get_%s_distribution' % distribution['type'])(cr, uid, distribution['id'], date, res_ids, context)

    def apply_distribution_keys(self, cr, uid, distribution_id, line_vals, context=None):
        assert isinstance(distribution_id, (int, long)), 'distribution_id must be an integer'
        assert line_vals and isinstance(line_vals, dict), 'line_vals must be a dictionary'
        res = []
        distribution = self.browse(cr, uid, distribution_id, context)
        column_src = distribution.axis_src_id.column_label
        column_dest = distribution.axis_dest_id.column_label
        res_ids = line_vals.get(column_src) and [line_vals[column_src]] or []
        distribution_keys = self.get_distribution(cr, uid, distribution_id, line_vals.get('date'), res_ids, context)
        if not distribution_keys:
            res = [line_vals]
        else:# elif distribution_keys:
            axis_src_item_id = line_vals.get(column_src)
            for axis_dest_item_id in distribution_keys.get(axis_src_item_id, []):
                rate = distribution_keys[axis_src_item_id][axis_dest_item_id]['rate'] / 100
                key_id = distribution_keys[axis_src_item_id][axis_dest_item_id]['key_id']
                new_vals = dict(line_vals)
                new_vals.update({
                    column_dest: axis_dest_item_id,
                    'amount': line_vals.get('amount', 0.0) * rate,
                    'unit_amount': line_vals.get('unit_amount', 0.0) * rate,
                    'amount_currency': line_vals.get('amount_currency', 0.0) * rate,
                    'distribution_keys': line_vals.get('distribution_keys') and '%s,%s' % (line_vals['distribution_keys'], key_id) or '%s' % key_id,
                })
                res.append(new_vals)
        return res
AnalyticDistribution()

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
            domain = [('id', '<>', period.id)]
            if period.date_start:
                domain += ['|', ('date_stop', '>=', period.date_start), ('date_stop', '=', False)]
            if period.date_stop:
                domain += ['|', ('date_start', '>=', period.date_stop), ('date_start', '=', False)]
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
        context = dict(context or {})
        if context.get('distribution_id'):
            del context['distribution_id']
        res = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        for key in self.read(cr, uid, ids, ['axis_src_item_id', 'axis_dest_item_id', 'period_id'], context):
            distribution = self.pool.get('account.analytic.distribution.period').browse(cr, uid, key['period_id'][0], context).distribution_id
            axis_src_item_id = key['axis_src_item_id']
            axis_dest_item_id = key['axis_dest_item_id']
            axis_src_item_name = self.pool.get(distribution.axis_src_id.model).name_get(cr, uid, [axis_src_item_id], context)
            axis_dest_item_name = self.pool.get(distribution.axis_dest_id.model).name_get(cr, uid, [axis_dest_item_id], context)
            res[key['id']] = {
                'axis_src_item_name': axis_src_item_name and axis_src_item_name[0][1] or '',
                'axis_dest_item_name': axis_dest_item_name and axis_dest_item_name[0][1] or '',
            }
        return res

    _columns = {
        'period_id': fields.many2one('account.analytic.distribution.period', 'Distribution Application Period', required=True, ondelete='cascade'),
        'axis_src_item_id': fields.integer('Item of Source Axis', required=True),
        'axis_src_item_name': fields.function(_get_items, method=True, type='char', string='Item of Source Axis', readonly=True, multi='distribution_key'),
        'axis_dest_item_id': fields.integer('Item of Destination Axis', required=True),
        'axis_dest_item_name': fields.function(_get_items, method=True, type='char', string='Item of Destination Axis', readonly=True, multi='distribution_key'),
        'rate': fields.float('Rate (%)', digits=(1, 2), required=True),
        'company_id': fields.related('period_id', 'distribution_id', 'company_id', type='many2one', relation='res.company', string='Company', readonly=True),
        'active': fields.boolean('Active', readonly=True),
        'date_start': fields.date('Start Date', readonly=True),
        'date_stop': fields.date('End Date', readonly=True),
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
                        res[field] = model_obj.name_get(cr, uid, res[field], context)[0]
                    elif isinstance(res, list):
                        for index in range(len(res)):
                            obj_name = model_obj.name_get(cr, uid, [res[index][field]], context)
                            res[index][field] = obj_name and obj_name[0] or ''
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
                        'type': 'many2one',
                        'relation': axis.model,
                        'domain': axis.domain and eval(axis.domain),
                    })
        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(AnalyticDistributionKey, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        if view_type == 'form':
            res['arch'] = """<form string="Distribution Key">
    <field name="axis_src_item_id"/>
    <field name="axis_dest_item_id"/>
    <field name="rate"/>
</form>"""
        return res

    def _deactivate_old_key(self, cr, uid, key_id, context=None):
        context = context or {}
        context['distribution_key_deactivation_in_progress'] = True
        key = self.browse(cr, uid, key_id)#Do not pass context in order to have integer type fields
        domain = [
            ('id', '!=', key.id),
            ('period_id', '=', key.period_id.id),
            ('axis_src_item_id', '=', key.axis_src_item_id),
            ('axis_dest_item_id', '=', key.axis_dest_item_id),
        ]
        old_key_ids = self.search(cr, uid, domain, context={'active_test': True})
        if old_key_ids:
            self.write(cr, uid, old_key_ids, {'active': False, 'date_stop': time.strftime('%Y-%m-%d')}, context)
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
        for key in self.browse(cr, uid, ids):#Do not pass context in order to have integer type fields
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
        'distribution_ids': fields.many2many('account.analytic.distribution', 'analytic_distribution_journal_rel', 'journal_id', 'distribution_id', 'Distributions'),
    }
AnalyticJournal()

class AnalyticLine(osv.osv):
    _inherit = 'account.analytic.line'

    def __init__(self, pool, cr):
        super(AnalyticLine, self).__init__(pool, cr)
        if self._columns.has_key('account_id'):
            self._columns['account_id'].required = False

    _columns = {
        'distribution_keys': fields.char('Distribution keys', size=64),
    }

    def _distribute(self, cr, uid, vals, context=None):
        res = [vals]
        if vals.get('journal_id'):
            distribution_ids = self.pool.get('account.analytic.journal').read(cr, uid, vals['journal_id'], ['distribution_ids'], context)['distribution_ids']
            distribution_obj = self.pool.get('account.analytic.distribution')
            while distribution_ids:
                for distrib in distribution_obj.browse(cr, uid, distribution_ids, context):
                    if res[0].get(distrib.axis_src_id.column_label):
                        if not res[0].get(distrib.axis_dest_id.column_label):
                            new_res = []
                            for line_vals in res:
                                new_res.extend(distribution_obj.apply_distribution_keys(cr, uid, distrib.id, line_vals, context))
                            res = new_res
                        distribution_ids.remove(distrib.id)
        return res

    def create(self, cr, uid, vals, context=None):
        res_ids = []
        for new_vals in self._distribute(cr, uid, vals, context):
            res_ids.append(super(AnalyticLine, self).create(cr, uid, new_vals, context))
        return res_ids[0]
AnalyticLine()
