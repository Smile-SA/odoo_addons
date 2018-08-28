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
from tools.translate import _


class AnalyticForecastingWizard(osv.osv_memory):
    _name = 'account.analytic.forecasting.wizard'
    _description = 'Analytic Forecasting Wizard'
    _rec_name = 'measure'

    _columns = {
        'create_period_ids': fields.dummy(type='many2many', relation='account.analytic.period', string="Reference Periods", required=True),
        'period_ids': fields.dummy(type='many2many', relation='account.analytic.period', string="Analysis Periods", required=True),
        'field_ids': fields.dummy(type='many2many', relation='ir.model.fields', string="Visible Fields", domain=[
            ('model', '=', 'account.analytic.line'),
            ('name', 'not in', ('period_id', 'analysis_period_id', 'type')),
            ('ttype', '!=', 'float'),
        ]),
        'x_axis': fields.selection([
            ('period_ids', 'Analysis Periods'),
            ('create_period_ids', 'Reference Periods'),
        ], "X-axis", required=True),
        'measure': fields.selection([
            ('amount', 'Amount'),
            ('unit_amount', 'Quantity'),
            ('ratio', 'Ratio'),
        ], "Measure", required=True),
    }

    _defaults = {
        'measure': 'amount',
        'x_axis': 'period_ids',
    }

    def create(self, cr, uid, vals, context=None):
        res_id = super(AnalyticForecastingWizard, self).create(cr, uid, vals, context)
        self.datas[res_id] = {}
        vals = vals or {}
        for key in vals:
            if isinstance(vals[key], list):
                self.datas[res_id][key] = vals[key][0][2]
            else:
                self.datas[res_id][key] = vals[key]
        return res_id

    def button_open_window(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'ids length should be equal to 1.'
        context = context or {}
        context.update(self.datas[ids[0]])
        context['from_analytic_forecasting_wizard'] = True
        return {
            'name': 'Analytic Lines Analysis',
            'type': 'ir.actions.act_window',
            'res_model': 'account.analytic.forecasting.report',
            'view_type': 'form',
            'view_mode': 'tree',
            'context': context,
        }
AnalyticForecastingWizard()

PERIOD_FIELDS = ['create_period_id', 'period_id']


def _get_period_ids_for_dynamic_columns(context):
    return context[context['x_axis']]


def _get_dynamic_columns(context):
    x_axis = context.get('x_axis', '')
    dynamic_columns = []
    if context.get(x_axis):
        dynamic_columns.extend([x_axis.replace('ids', str(period_id)) for period_id in _get_period_ids_for_dynamic_columns(context)])
    return dynamic_columns


def _get_static_period_field(context):
    x_axis = context['x_axis'][: -1]
    static_period = ''
    for field in PERIOD_FIELDS:
        if field != x_axis:
            static_period = field
    return static_period


def _get_period_ids_to_restrict_domain(context):
    return context['%ss' % _get_static_period_field(context)]


class AnalyticForecastingReport(osv.osv):
    _name = 'account.analytic.forecasting.report'
    _description = 'Analytic Forecasting Report'
    _inherit = 'account.analytic.line'
    _table = 'account_analytic_line'

    def create(self, cr, uid, vals, context=None):
        raise osv.except_osv(_('Error'), _('You cannot add an entry of this view!'))

    def write(self, cr, uid, ids, vals, context=None):
        raise osv.except_osv(_('Error'), _('You cannot modify an entry of this view!'))

    def unlink(self, cr, uid, ids, context=None):
        raise osv.except_osv(_('Error'), _('You cannot delete an entry of this view!'))

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        return self.pool.get(self._inherit).read_group(cr, uid, domain, fields, groupby, offset, limit, context, orderby)

    def _search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False, access_rights_uid=None):
        args = args or []
        context = context or {}
        if context.get('x_axis'):
            args.append((context['x_axis'][: -1], 'in', _get_period_ids_to_restrict_domain(context)))
        return super(AnalyticForecastingReport, self)._search(cr, uid, args, offset, limit, order, context, count, access_rights_uid)

    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        fields = fields or []
        fields_to_read = []
        analysis_period_fields = []
        for field in fields:
            if field.startswith('period_'):
                analysis_period_fields.append(field)
            else:
                fields_to_read.append(field)
        fields_to_read.append('period_id')
        measures = []
        if context.get('measure'):
            if context['measure'] == 'ratio':
                measures = ['amount', 'unit_amount']
            else:
                measures = [context['measure']]
        fields_to_read.extend(measures)
        res = self.pool.get(self._inherit).read(cr, uid, ids, fields_to_read, context, load)
        for index, line_vals in enumerate(res):
            for field in analysis_period_fields:
                if field == 'period_%s' % line_vals['period_id'][0]:
                    line_vals[field] = line_vals[measures[0]] * line_vals.get(len(measures) > 1 and measures[1], 1.0)
                else:
                    line_vals[field] = 0.0
            for field_to_remove in ['period_id'] + measures:
                del line_vals[field_to_remove]
            res[index] = line_vals
        return res

    def fields_get(self, cr, uid, fields=None, context=None):
        res = self.pool.get(self._inherit).fields_get(cr, uid, fields, context)
        context = context or {}
        if context.get('origin') == 'fields_view_get':
            analytic_period_names = dict(self.pool.get('account.analytic.period').name_get(cr, uid, _get_period_ids_for_dynamic_columns(context),
                                                                                           context))
            for analytic_period_field in context['x_axis_period_fields']:
                res[analytic_period_field] = {
                    'type': 'float',
                    'string': analytic_period_names[int(analytic_period_field.replace(context['x_axis'][: -3], ''))],
                }
        return res

    def _get_x_axis_fields(self, cr, uid, context):
        x_axis_fields = [_get_static_period_field(context)]
        if context.get('field_ids'):
            for field in self.pool.get('ir.model.fields').read(cr, uid, context['field_ids'], ['name'], context):
                x_axis_fields.append(field['name'])
        return x_axis_fields

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        context = context or {}
        if not context.get('from_analytic_forecasting_wizard') or view_type != 'tree':
            return self.pool.get(self._inherit).fields_view_get(cr, uid, False, view_type, context, toolbar, submenu)
        else:
            res = {'type': 'tree', 'model': self._name, 'name': 'default', 'field_parent': False, 'view_id': 0}
            context = context or {}
            context['origin'] = 'fields_view_get'
            x_axis_fields = self._get_x_axis_fields(cr, uid, context)
            context['x_axis_period_fields'] = x_axis_period_fields = _get_dynamic_columns(context)
            res['fields'] = self.fields_get(cr, uid, x_axis_fields, context)
            res['arch'] = """<?xml version="1.0" encoding="utf-8"?>
<tree string="Analytic Forecasting Analysis">
"""
            for field in x_axis_fields + x_axis_period_fields:
                res['arch'] += '    <field name="%s"/>\n' % field
            res['arch'] += '</tree>'
            return res
AnalyticForecastingReport()
