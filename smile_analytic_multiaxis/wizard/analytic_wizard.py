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


class AnalyticDistributionKeyWizard(osv.osv):
    _name = 'account.analytic.distribution.key.wizard'
    _description = 'Analytic Distribution Key Wizard'
    _inherit = 'account.analytic.distribution.key'
    _table = 'account_analytic_distribution_key'

    def create(self, cr, uid, vals, context=None):
        total_rate = sum([vals[k] for k in vals if k.startswith('axis_dest_item_id_')])
        if total_rate != 100.00:
            raise osv.except_osv(_('Error'), _('A distribution key is complete only if total rate is equal to 100% !'))
        cr.execute("SELECT id, axis_dest_item_id, rate FROM account_analytic_distribution_key WHERE axis_src_item_id = %s "
                   "AND active = TRUE", (vals['axis_src_item_id'], ))
        old_keys = dict([(item[1], {'rate': item[2], 'key_id': item[0]}) for item in cr.fetchall()])
        key_obj = self.pool.get(self._inherit)
        for item_id in (int(k.replace('axis_dest_item_id_', '')) for k in vals if k.startswith('axis_dest_item_id_')):
            if item_id in old_keys:
                if vals['axis_dest_item_id_%s' % item_id] != old_keys[item_id]['rate']:
                    key_obj.write(cr, uid, old_keys[item_id]['key_id'], {'rate': vals['axis_dest_item_id_%s' % item_id]}, context)
            else:
                key_obj.create(cr, uid, {
                    'period_id': vals['period_id'],
                    'axis_src_item_id': vals['axis_src_item_id'],
                    'axis_dest_item_id': item_id,
                    'rate': vals['axis_dest_item_id_%s' % item_id],
                }, context)
        return 42

    def unlink(self, cr, uid, ids, context=None):
        raise osv.except_osv(_('Error'), _('You cannot delete distribution keys!'))

    def _search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False, access_rights_uid=None):
        res = []
        args = args or []
        context = context or {}
        if context.get('default_distribution_id'):
            args.append(('period_id.distribution_id', '=', context['default_distribution_id']))
        key_ids = self.pool.get(self._inherit).search(cr, uid, args, offset, limit, order, context)
        if key_ids:
            cr.execute('SELECT axis_src_item_id FROM ' + self._table + ' WHERE id IN %s GROUP BY axis_src_item_id', (tuple(key_ids), ))
            res = cr.fetchall()
            res = [item[0] for item in res]
        return count and len(res) or res

    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        res = {}
        initial_type = type(ids)
        if isinstance(ids, (int, long)):
            ids = [ids]
        domain = [('axis_src_item_id', 'in', ids)]
        context = context or {}
        if context.get('distribution_id'):
            if isinstance(context['distribution_id'], basestring):
                module, xml_id = context['distribution_id'].split('.')
                context['distribution_id'] = self.pool.get('ir.model.data').get_object_reference(cr, uid, module, xml_id)
            domain.append(('period_id.distribution_id', '=', context['distribution_id']))
        key_obj = self.pool.get(self._inherit)
        key_ids = key_obj.search(cr, uid, domain, context=context)
        for key in key_obj.browse(cr, uid, key_ids):  # Do not pass context in order to obtain integer fields
            res.setdefault(key.axis_src_item_id, {}).update({
                'id': key.axis_src_item_id,
                'period_id': self.pool.get(key.period_id._name).name_get(cr, uid, [key.period_id.id], context)[0],
                'axis_src_item_id': self.pool.get(key.period_id.distribution_id.axis_src_id.model).name_get(cr, uid, [key.axis_src_item_id],
                                                                                                            context)[0],
                'axis_dest_item_id_%s' % key.axis_dest_item_id: key.rate,
                'axis_dest_item_id': key.axis_dest_item_id,
                'rate': key.rate,
            })
            res[key.axis_src_item_id].setdefault('keys_count', 0)
            res[key.axis_src_item_id]['keys_count'] += 1
        return initial_type in (int, long) and res.values()[0] or res.values()

    def fields_get(self, cr, uid, fields=None, context=None):
        context = context or {}
        if context.get('distribution_id'):
            if isinstance(context['distribution_id'], basestring):
                module, xml_id = context['distribution_id'].split('.')
                context['distribution_id'] = self.pool.get('ir.model.data').get_object_reference(cr, uid, module, xml_id)
            res = self.pool.get(self._inherit).fields_get(cr, uid, ['period_id', 'axis_src_item_id', 'axis_dest_item_id', 'rate'], context)
            distrib = self.pool.get('account.analytic.distribution').browse(cr, uid, context['distribution_id'], context)
            res['axis_src_item_id']['string'] = distrib.axis_src_id.model_id.name
            model_obj = self.pool.get(distrib.axis_dest_id.model)
            item_ids = model_obj.search(cr, uid, [], context={'active_test': True})
            item_names = dict(model_obj.name_get(cr, uid, item_ids, context))
            for item_id in item_ids:
                res['axis_dest_item_id_%s' % item_id] = {
                    'string': item_names[item_id],
                    'type': 'float',
                }
            res['keys_count'] = {
                'string': _("Keys"),
                'type': 'integer',
            }
            return res
        return self.pool.get(self._inherit).fields_get(cr, uid, fields, context)

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = {}
        context = context or {}
        if context.get('distribution_id') and view_type in ('tree', 'form'):
            if isinstance(context['distribution_id'], basestring):
                module, xml_id = context['distribution_id'].split('.')
                context['distribution_id'] = self.pool.get('ir.model.data').get_object_reference(cr, uid, module, xml_id)
            res['fields'] = self.fields_get(cr, uid, context=context)
            if view_type == 'form':
                res['arch'] = """<form string="%s">
                                     <field name="period_id" invisible="1" colspan="4"/>\n""" % _('Distribution Key')
                axis_dest_model = ''
                context = context or {}
                if context.get('distribution_id'):
                    distrib = self.pool.get('account.analytic.distribution').browse(cr, uid, context['distribution_id'], context)
                    axis_dest_model = distrib.axis_dest_id.model_id.name
                if context.get('show_axis_src_item') or context.get('distribution_type') == 'specific':
                    res['arch'] += """    <separator string="%s" colspan="4"/>
                                          <field name="axis_src_item_id" colspan="4" required="1"/>""" % _('Source')
                res['arch'] += """    <separator string="%s%s" colspan="4"/>\n""" % (_('Target'), axis_dest_model and ': %s' % axis_dest_model or '')
                for field in res['fields']:
                    if field.startswith('axis_dest_item_id'):
                        res['arch'] += '    <field name="%s"/>\n' % field
                res['arch'] += '</form>'
            else:
                if not context.get('show_axis_src_item') or context.get('distribution_type') == 'global':
                    res['arch'] = """<tree string="%s">
                                         <field name="axis_dest_item_id"/>
                                         <field name="rate"/>
                                     </tree>""" % _("Distribution Keys")
                else:
                    res['arch'] = """<tree string="%s">
                                         <field name="axis_src_item_id"/>
                                         <field name="keys_count"/>
                                     </tree>""" % _("Distribution Keys")
        else:
            res = self.pool.get(self._inherit).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        res.update({'name': 'default', 'model': self._name, 'view_id': 0})
        return res

    def default_get(self, cr, uid, fields_list, context=None):
        context = context or {}
        if context.get('default_period_id') and isinstance(context['default_period_id'], basestring):
            module, xml_id = context['default_period_id'].split('.')
            context['default_period_id'] = self.pool.get('ir.model.data').get_object_reference(cr, uid, module, xml_id)
        return super(AnalyticDistributionKeyWizard, self).default_get(cr, uid, fields_list, context)
AnalyticDistributionKeyWizard()


class AnalyticDistributionPeriod(osv.osv):
    _inherit = 'account.analytic.distribution.period'

    def _get_key_wizards(self, cr, uid, ids, name, arg, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = {}
        for period_id in ids:
            res[period_id] = self.pool.get('account.analytic.distribution.key.wizard').search(cr, uid, [('period_id', '=', period_id)],
                                                                                              context=context)
        return res

    def _set_key_wizards(self, cr, uid, ids, field_name, field_value, arg, context=None):
        if field_name == 'key_wizard_ids':
            self.pool.get('account.analytic.distribution.key.wizard').create(cr, uid, vals=field_value[0][2], context=context)
        return True

    _columns = {
        'key_wizard_ids': fields.function(_get_key_wizards, fnct_inv=_set_key_wizards, method=True, type='one2many',
                                          relation='account.analytic.distribution.key.wizard', string="Keys", store=False),
    }
AnalyticDistributionPeriod()

#class AnalyticDistributionKey(osv.osv):
#    _inherit = 'account.analytic.distribution.key'
#
#    _columns = {
#        'origin': fields.char('Origin', size=128),  # Can be useful if you want to define a distribution key from an other object form view
#    }
#AnalyticDistributionKey()

########## SAMPLE  ##########
#    <field colspan="4" name="distribution_key_ids" mode="form" nolabel="1"
#        context="{'distribution_id': 3, 'default_period_id': 11, 'default_axis_src_item_id': active_id}"/>
#class InvoiceLine(osv.osv):
#    _inherit = 'account.invoice.line'
#
#    def _get_key_wizards(self, cr, uid, ids, name, arg, context=None):
#        if isinstance(ids, (int, long)):
#            ids = [ids]
#        res = {}
#        for line_id in ids:
#            res[line_id] = self.pool.get('account.analytic.distribution.key.wizard').search(cr, uid, [
#                ('axis_src_model', '=', self._name), ('axis_src_item_id', '=', line_id),
#            ], context=context)
#        return res
#
#    def _set_key_wizards(self, cr, uid, ids, field_name, field_value, arg, context=None):
#        if field_name == 'distribution_key_ids':
#            vals = field_value[0][2]
#            if not vals.get('axis_src_item_id'):
#                vals['axis_src_item_id'] = isinstance(ids, (list, tuple)) and ids[0] or ids
#            self.pool.get('account.analytic.distribution.key.wizard').create(cr, uid, vals, context)
#        return True
#
#    _columns = {
#        'distribution_key_ids': fields.function(_get_key_wizards, fnct_inv=_set_key_wizards, method=True, type='one2many',
#                                                relation='account.analytic.distribution.key.wizard', string="Keys", store=False),
#    }
#InvoiceLine()
