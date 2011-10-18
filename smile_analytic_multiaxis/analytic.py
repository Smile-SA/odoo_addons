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
    _name = 'account.analytic.axis'
    _description = 'Analytic Axis'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'ref': fields.char('Analytic line column label', size=64, required=True),
        'active': fields.boolean('Active'),
        'model_id': fields.many2one('ir.model', 'Object', domain=[('osv_memory', '=', False)], required=True, ondelete='restrict'),
        'model': fields.related('model_id', 'model', type='char', string="Model"),
        'domain': fields.char("Domain", size=256, required=True),
        'required': fields.boolean('Required'),
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
        for axis in self.read(cr, 1, ids, context=context):
            if (not axis['active'] or context.get('ids_to_unlink')) and axis['ref'] in line_obj._columns:
                del line_obj._columns[axis['ref']]
            elif axis['active']:
                line_obj._columns[axis['ref']] = fields.many2one(axis['model'], axis['name'], \
                    domain=axis['domain'] and eval(axis['domain']) or [], required=axis['required'])
        line_obj._auto_init(cr, context)
        return True

    def __init__(self, pool, cr):
        super(AnalyticAxis, self).__init__(pool, cr)
        self._update_analytic_line_columns(cr)

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
        context['ids_to_unlink'] = True
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
        'version_ids': fields.one2many('account.analytic.distribution.version', 'distribution_id', 'Versions'),
        'company_id': fields.many2one('res.company', 'Company'),
    }

    _defaults = {
        'active': True,
    }
AnalyticDistribution()

class AnalyticDistributionVersion(osv.osv):
    _name = 'account.analytic.distribution.version'
    _description = 'Analytic Distribution Version'

    _columns = {
        'distribution_id': fields.many2one('account.analytic.distribution', 'Distribution', required=True),
#        'active': fields.date('Active'),
        'date_start': fields.date('Start Date'),
        'date_end': fields.date('End Date'),
        'item_ids': fields.one2many('account.analytic.distribution.version.item', 'version_id', 'Keys'),
        'company_id': fields.related('distribution_id', 'company_id', type='many2one', relation='res.company', string='Company', readonly=True),
    }

    def _check_versions_overlap(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for version in self.browse(cr, uid, ids, context):
            domain = [
                ('id', '<>', version.id),
                '|', '|',
                '&', ('date_start', '>=', version.date_start), ('date_start', '<=', version.date_end),
                '&', ('date_end', '>=', version.date_start), ('date_end', '<=', version.date_end),
                '&', ('date_start', '<=', version.date_start), ('date_end', '>=', version.date_end),
            ]
            if self.search(cr, uid, domain, context={'active_test': True}):
                return False
        return True

    _constraints = [
        (_check_versions_overlap, 'Some versions overlap!', ['date_start', 'date_end']),
    ]
AnalyticDistributionVersion()

class AnalyticDistributionItem(osv.osv):
    _name = 'account.analytic.distribution.item'
    _description = 'Analytic Distribution Key'

    _columns = {
        'version_id': fields.many2one('account.analytic.distribution.version', 'Distribution Version', required=True),
        'axis_src_item_id': fields.integer('Item of Source Axis', required=True),
        'axis_dest_item_id': fields.integer('Item or Destination Axis', required=True),
        'rate': fields.float('Rate (%)', digits=(1, 2), required=True),
        'company_id': fields.related('version_id', 'distribution_id', 'company_id', type='many2one', relation='res.company', string='Company', readonly=True),
        # Useful ?
        'active': fields.date('Active'),
        'date_start': fields.date('Start Date'),
        'date_end': fields.date('End Date'),
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
                            res[index][field] = model_obj.name_get(cr, uid, res[index][field], context)[0]
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
                        'context': context,
                    })
        return res
AnalyticDistributionItem()
