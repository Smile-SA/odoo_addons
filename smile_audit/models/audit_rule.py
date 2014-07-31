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

from openerp import api, fields, models, SUPERUSER_ID, tools, _
from openerp.modules.registry import RegistryManager
from openerp.tools.func import wraps

_logger = logging.getLogger(__package__)


def _get_args(method, *args, **kwargs):
    context = kwargs.get('context')
    if method == 'create':
        vals, ids = args[0], []
    if method == 'write':
        ids, vals = args[:2]
    if method == 'unlink':
        ids, vals = args[0], {}
    if isinstance(ids, (int, long)):
        ids = [ids]
    return ids, vals, context


def audit_decorator(origin):
    @wraps(origin)
    def audit_wrapper(obj, cr, uid, *args, **kwargs):
        method = origin.__name__
        ids, vals, context = _get_args(method, *args, **kwargs)
        rule_obj = obj.pool['audit.rule']
        rule_ids = rule_obj.search(cr, SUPERUSER_ID, [('model_id.model', '=', obj._model)], limit=1)
        if rule_ids:
            old_values = None
            if method != 'create':
                old_values = obj.read(cr, uid, ids, vals.keys(), context, load='_classic_write')
                if method == 'unlink':
                    rule_obj.log(cr, uid, rule_ids, method, old_values)
        result = origin(cr, uid, *args, **kwargs)  # WARNING: do not pass obj added by api.old_api
        if rule_ids:
            new_values = None
            if audit_wrapper.origin.__name__ != 'unlink':
                if method == 'create':
                    ids = [result]
                new_values = obj.read(cr, uid, ids, vals.keys(), context, load='_classic_write')
                rule_obj.log(cr, uid, rule_ids, method, old_values, new_values)
        return result
    return audit_wrapper


class AuditRule(models.Model):
    _name = 'audit.rule'
    _description = 'Audit Rule'

    name = fields.Char(size=32, required=True)
    active = fields.Boolean(default=True)
    log_create = fields.Boolean('Log Creation', default=True)
    log_write = fields.Boolean('Log Update', default=True)
    log_unlink = fields.Boolean('Log Deletion', default=True)
    model_id = fields.Many2one('ir.model', 'Object', required=True,
                               help='Select object for which you want to generate log.',
                               domain=[('model', 'not in', ('audit.log', 'audit.log.line'))])
    action_id = fields.Many2one('ir.actions.act_window', 'Client Action', readonly=True)
    values_id = fields.Many2one('ir.values', 'Client Action Link', readonly=True)

    _sql_constraints = [
        ('model_uniq', 'unique(model_id)', 'There is already a rule defined on this object.\n'
         'You cannot define another: please edit the existing one.'),
    ]

    @api.one
    def _add_action(self):
        if not self.action_id:
            vals = {
                'name': _('View logs'),
                'res_model': 'audit.log',
                'src_model': self.model_id.model,
                'domain': "[('model_id','=', %s), ('res_id', '=', active_id)]" % self.model_id.id,
            }
            self.action_id = self.env['ir.actions.act_window'].create(vals)

    @api.one
    def _add_values(self):
        if not self.values_id:
            self.env['ir.model.data'].ir_set('action', 'client_action_relate', 'view_log_' + self.model_id.model,
                                             [self.model_id.model], 'ir.actions.act_window,%s' % self.action_id,
                                             replace=True, isobject=True, xml_id=False)
            values = self.env['ir.values'].search([('model', '=', self.model_id.model),
                                                   ('value', '=', 'ir.actions.act_window,%s' % self.action_id)])
            if values:
                self.values_id = values[0]

    @api.one
    def _activate(self):
        if self.env.context and \
                self.env.context.get('activation_in_progress'):
            return
        self = self.with_context(activation_in_progress=True)
        self._add_action()
        self._add_values()

    @api.one
    def _deactivate(self):
        if self.values_id:
            self.values_id.unlink()
        if self.action_id:
            self.action_id.unlink()

    def _register_hook(self, cr, ids=None):
        if not ids:
            ids = self.search(cr, SUPERUSER_ID, [])
        for rule in self.browse(cr, SUPERUSER_ID, ids):
            model_obj = self.pool[rule.model_id.model]
            if not hasattr(model_obj, 'audit_rule'):
                for method in ('create', 'write', 'unlink'):
                    model_obj._patch_method(method, audit_decorator(getattr(model_obj, method)))
                model_obj.audit_rule = True
                updated = True
        return updated

    @api.multi
    def update_rule(self, force_deactivation=False):
        for rule in self:
            if rule.active and not force_deactivation:
                rule._activate()
            else:
                rule._deactivate()
        if self._register_hook(self.env.cr, self):
            RegistryManager.signal_registry_change(self.env.cr.dbname)
        return True

    @api.model
    @api.returns('self')
    def create(self, vals):
        rule = super(AuditRule, self).create(vals)
        rule.update_rule()
        return rule

    @api.multi
    def write(self, vals):
        res = super(AuditRule, self).write(vals)
        self.update_rule()
        return res

    @api.multi
    def unlink(self):
        self.update_rule(force_deactivation=True)
        return super(AuditRule, self).unlink()

    @api.model
    def _get_log_lines(self, old_values, new_values):
        line_vals = []
        keys = set(old_values) | set(new_values)
        for key in keys:
            old_value = old_values.get(key) or ''
            new_value = new_values.get(key) or ''
            if old_value != new_value:
                line_vals.append({
                    'field_name': key,
                    'old_value': old_value,
                    'new_value': new_value,
                })
        return line_vals

    @api.one
    def log(self, method, old_values=None, new_values=None):
        _logger.debug('Starting audit log')
        data = {}
        old_values = old_values or []
        new_values = new_values or []
        for vals in old_values:
            data.setdefault(vals['id'], {'old': {}, 'new': {}})['old'] = vals
        for vals in new_values:
            data.setdefault(vals['id'], {'old': {}, 'new': {}})['new'] = vals
        for res_id in data:
            line_vals = self._get_log_lines(data[res_id]['old'], data[res_id]['new'])
            if line_vals:
                self.env['audit.log'].sudo().create({
                    'user_id': self.env.uid,
                    'model_id': self.model_id.id,
                    'method': method,
                    'res_id': res_id,
                    'line_ids': [(0, 0, vals) for vals in line_vals],
                })
        return True
