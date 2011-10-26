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
        'ref': fields.char('Analytic line column label', size=55, required=True),
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

    def _check_ref(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for axis in self.read(cr, uid, ids, ['ref'], context):
            for character in axis['ref']:
                if character not in 'abcdefghijklmnopqrstuvwxyz0123456789_':
                    return False
        return True

    _constraints = [
        (_check_ref, 'Analytic line column label is only composed of alphanumeric characters and underscore', ['ref']),
    ]

    def _update_analytic_line_columns(self, cr, ids=None, context=None):
        context = context or {}

        if isinstance(ids, (int, long)):
            ids = [ids]
        if not ids:
            ids = self.search(cr, 1, [], context={'active_test': False})

        line_obj = self.pool.get('account.analytic.line')
        for axis in self.browse(cr, 1, ids, context):
            if (not axis.active or context.get('unlink_axis')) and axis.ref in line_obj._columns:
                del line_obj._columns[axis.ref]
                if axis.field_ids:
                    for field in axis.field_ids:
                        column = '%s_%s' % (axis.ref, field.id)
                        if column in line_obj._columns:
                            del line_obj._columns[column]
            elif axis.active:
                line_obj._columns[axis.ref] = fields.many2one(axis.model, axis.name, \
                    domain=axis.domain and eval(axis.domain) or [], required=axis.required)
                if axis.field_ids:
                    for field in axis.field_ids:
                        column = '%s_%s' % (axis.ref, field.id)
                        line_obj._columns[column] = fields.related(axis.ref, field.name, \
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
        'axis_src_id': fields.many2one('account.analytic.axis', 'Source Axis', required=True),
        'axis_dest_id': fields.many2one('account.analytic.axis', 'Destination Axis', required=True),
        'period_ids': fields.one2many('account.analytic.distribution.period', 'distribution_id', 'Application Periods'),
        'company_id': fields.many2one('res.company', 'Company'),
    }

    _defaults = {
        'active': True,
    }
AnalyticDistribution()

class AnalyticDistributionApplicationPeriod(osv.osv):
    _name = 'account.analytic.distribution.period'
    _description = 'Analytic Distribution Application Period'
    _rec_name = 'distribution_id'

    _columns = {
        'distribution_id': fields.many2one('account.analytic.distribution', 'Distribution', required=True),
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
AnalyticDistributionApplicationPeriod()

class AnalyticDistributionItem(osv.osv):
    _name = 'account.analytic.distribution.key'
    _description = 'Analytic Distribution Key'
    _rec_name = 'period_id'

    def _get_items(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        for key in self.browse(cr, uid, ids, context):
            distribution = key.period_id.distribution_id
            axis_src_item_id = isinstance(key.axis_src_item_id, tuple) and key.axis_src_item_id[0] or key.axis_src_item_id
            axis_dest_item_id = isinstance(key.axis_dest_item_id, tuple) and key.axis_dest_item_id[0] or key.axis_dest_item_id
            axis_src_item_name = self.pool.get(distribution.axis_src_id.model).name_get(cr, uid, axis_src_item_id, context)
            axis_dest_item_name = self.pool.get(distribution.axis_dest_id.model).name_get(cr, uid, axis_dest_item_id, context)
            res[key.id] = {
                'axis_src_item_name': axis_src_item_name and axis_src_item_name[0][1] or '',
                'axis_dest_item_name': axis_dest_item_name and axis_dest_item_name[0][1] or '',
            }
        return res

    _columns = {
        'period_id': fields.many2one('account.analytic.distribution.period', 'Distribution Application Period', required=True),
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
        res = super(AnalyticDistributionItem, self).read(cr, uid, ids, allfields, context, load)
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
                            obj_name = model_obj.name_get(cr, uid, res[index][field], context)
                            res[index][field] = obj_name and obj_name[0] or ''
        return res

    def fields_get(self, cr, uid, allfields=None, context=None):
        res = super(AnalyticDistributionItem, self).fields_get(cr, uid, allfields, context)
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
        res = super(AnalyticDistributionItem, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
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
        new_key_id = super(AnalyticDistributionItem, self).create(cr, uid, vals, context)
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
            return super(AnalyticDistributionItem, self).write(cr, uid, ids, vals, context)

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
        return super(AnalyticDistributionItem, self).unlink(cr, uid, ids, context)
AnalyticDistributionItem()
