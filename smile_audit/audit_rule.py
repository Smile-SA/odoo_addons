# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging

from openerp import SUPERUSER_ID, tools
from openerp.modules.registry import Registry
from openerp.osv import fields, orm
from openerp.tools.translate import _

from audit_decorator import audit_decorator, cache_restarter

_logger = logging.getLogger(__package__)


class AuditRule(orm.Model):
    _name = 'audit.rule'
    _description = 'Audit Rule'
    _decorated_methods = {}

    def __init__(self, pool, cr):
        super(AuditRule, self).__init__(pool, cr)
        cr.execute("SELECT relname FROM pg_class WHERE relname=%s", (self._table,))
        setattr(Registry, 'load', cache_restarter(getattr(Registry, 'load')))

    _columns = {
        'name': fields.char('Name', size=32, required=True),
        'model_id': fields.many2one('ir.model', 'Object', required=True, help='Select object for which you want to generate log.',
                                    domain=[('model', 'not in', ('audit.log', 'audit.log.line'))]),
        'model': fields.related('model_id', 'model', type='char', size=64, readonly=True, store={
            'audit.rule': (lambda self, cr, uid, ids, context=None: ids, ['model_id'], 20),
        }),
        'active': fields.boolean('Active'),
        'log_create': fields.boolean('Log Creation'),
        'log_write': fields.boolean('Log Update'),
        'log_unlink': fields.boolean('Log Deletion'),
        'action_id': fields.many2one('ir.actions.act_window', 'Client Action', readonly=True),
        'values_id': fields.many2one('ir.values', 'Client Action Link', readonly=True),
    }

    _defaults = {
        'active': True,
        'log_create': True,
        'log_write': True,
        'log_unlink': True,
    }

    _sql_constraints = [
        ('model_uniq', 'unique(model_id)', 'There is already a rule defined on this object.\n'
         'You cannot define another: please edit the existing one.'),
    ]

    def _activate_client_action(self, cr, uid, rule, context=None):
        context = context or {}
        if context.get('client_activation_in_progress'):
            return True
        action_id = rule.action_id.id
        values_id = rule.values_id.id
        if not action_id:
            vals = {
                'name': _('View logs'),
                'res_model': 'audit.log',
                'src_model': rule.model,
                'domain': "[('model_id','=', %s), ('res_id', '=', active_id)]" % rule.model_id.id,
            }
            action_id = self.pool.get('ir.actions.act_window').create(cr, uid, vals, context)
        if not values_id:
            self.pool.get('ir.model.data').ir_set(cr, uid, 'action', 'client_action_relate', 'view_log_' + rule.model, [rule.model],
                                                  'ir.actions.act_window,%s' % action_id, replace=True, isobject=True, xml_id=False)
            values_ids = self.pool.get('ir.values').search(cr, uid, [('model', '=', rule.model),
                                                                     ('value', '=', 'ir.actions.act_window,%s' % action_id)])
            if values_ids:
                values_id = values_ids[0]
        context['client_activation_in_progress'] = True
        return self.write(cr, uid, rule.id, {'action_id': action_id, 'values_id': values_id}, context)

    def _deactivate_client_action(self, cr, uid, rule, context=None):
        context = context or {}
        if rule.values_id:
            rule.values_id.unlink()
        if context.get('force_action_client_deletion') and rule.action_id:
            rule.action_id.unlink()
        return True

    def update_client_action(self, cr, uid, ids, context=None):
        uid = SUPERUSER_ID
        if isinstance(ids, (int, long)):
            ids = [ids]
        for rule in self.browse(cr, uid, ids, context):
            if rule.active:
                self._activate_client_action(cr, uid, rule, context)
            else:
                self._deactivate_client_action(cr, uid, rule, context)
        return True

    @tools.cache(skiparg=3)
    def _get_audit_rules(self, cr, uid):
        rules = {}
        ids = self.search(cr, SUPERUSER_ID, [])
        for rule in self.browse(cr, SUPERUSER_ID, ids):
            rules[rule.model] = dict([(log_method.replace('log_', ''), rule.id)
                                      for log_method in ('log_create', 'log_write', 'log_unlink')
                                      if getattr(rule, log_method)])
        return rules

    def check_rules(self, cr, uid, model, method, context=None):
        rules = self._get_audit_rules(cr, uid)
        return rules.get(model, {}).get(method, False)

    def create(self, cr, uid, vals, context=None):
        rule_id = super(AuditRule, self).create(cr, uid, vals, context)
        self.clear_caches()
        self.update_client_action(cr, uid, rule_id, context)
        return rule_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(AuditRule, self).write(cr, uid, ids, vals, context)
        self.clear_caches()
        self.update_client_action(cr, uid, ids, context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        context = context or {}
        context['force_client_action_deletion'] = True
        self.update_client_action(cr, uid, ids, context)
        res = super(AuditRule, self).unlink(cr, uid, ids, context)
        self.clear_caches()
        return res

    def _get_log_lines(self, cr, uid, rule, res_id, context):
        lines = []
        fields_list = context['fields_list']
        res_info = self.pool.get(rule.model).read(cr, uid, res_id, fields_list, context, '_classic_write')
        for field_name in fields_list:
            lines.append({
                'field_name': field_name,
                'old_value': context.get('old_values', {}).get(res_id, {}).get(field_name, ''),
                'new_value': context['method'] != 'unlink' and res_info[field_name] or '',
            })
        return lines

    def log(self, cr, uid, rule_id, context):
        _logger.debug('Starting audit log')
        log_obj = self.pool.get('audit.log')
        rule = self.browse(cr, SUPERUSER_ID, rule_id, context)
        for res_id in context.get('active_object_ids'):
            log_obj.create(cr, SUPERUSER_ID, {
                'user_id': uid,
                'model_id': rule.model_id.id,
                'method': context['method'],
                'res_id': res_id,
                'line_ids': [(0, 0, vals) for vals in self._get_log_lines(cr, uid, rule, res_id, context)],
            }, context)
        return True


orm.Model.create = audit_decorator(orm.Model.create)
orm.Model.write = audit_decorator(orm.Model.write)
orm.Model.unlink = audit_decorator(orm.Model.unlink)
