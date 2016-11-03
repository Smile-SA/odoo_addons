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

from odoo import api, fields, models, tools, _
from odoo.modules.registry import RegistryManager
from odoo.tools.safe_eval import safe_eval

from ..tools import audit_decorator

_logger = logging.getLogger(__package__)


class AuditRule(models.Model):
    _name = 'audit.rule'
    _description = 'Audit Rule'

    name = fields.Char(size=32, required=True)
    active = fields.Boolean(default=True)
    log_create = fields.Boolean('Log Creation', default=False)
    log_write = fields.Boolean('Log Update', default=True)
    log_unlink = fields.Boolean('Log Deletion', default=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], 'Status', default='draft', readonly=True)
    model_id = fields.Many2one('ir.model', 'Model', required=True,
                               help='Select model for which you want to generate log.',
                               domain=[('model', '!=', 'audit.log')],
                               readonly=True, states={'draft': [('readonly', False)]})
    action_id = fields.Many2one('ir.actions.act_window', 'Client Action', readonly=True)
    values_id = fields.Many2one('ir.values', "Add in the 'More' menu", readonly=True)

    _sql_constraints = [
        ('model_uniq', 'unique(model_id)', 'There is already a rule defined on this model.\n'
         'You cannot define another: please edit the existing one.'),
    ]

    @api.one
    def _add_action(self):
        if not self.action_id:
            vals = {
                'name': _('View audit logs'),
                'res_model': 'audit.log',
                'src_model': self.model_id.model,
                'domain': "[('model_id','=', %s), ('res_id', '=', active_id), ('method', 'in', %s)]"
                          % (self.model_id.id, [method for method in self._methods if not method.startswith("_")])
            }
            self.action_id = self.env['ir.actions.act_window'].create(vals)

    @api.one
    def _add_values(self):
        if not self.values_id:
            vals = {
                'name': 'view_log_' + self.model_id.model,
                'action_slot': 'client_action_relate',
                'model': self.model_id.model,
                'action': 'ir.actions.act_window,%s' % self.action_id.id,
                'res_id': False,
            }
            self.values_id = self.env['ir.values'].set_action(**vals)

    @api.one
    def _activate(self):
        if self._context and \
                self._context.get('activation_in_progress'):
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

    @api.multi
    def update_rule(self, force_deactivation=False):
        for rule in self:
            if rule.active and not force_deactivation:
                rule._activate()
            else:
                rule._deactivate()
        return True

    _methods = ['_create', '_write', 'unlink']

    @api.model
    @tools.ormcache()
    def _check_audit_rule(self):
        rules = self.sudo().search([])
        return {rule.model_id.model:
                {method.replace('_', ''): rule.id
                 for method in self._methods
                 if getattr(rule, 'log_%s' % method.replace('_', ''))}
                for rule in rules}

    @api.model_cr
    def _register_hook(self, ids=None):
        self = self.sudo()
        updated = False
        if ids:
            rules = self.browse(ids)
        else:
            rules = self.search([])
        for rule in rules:
            if rule.model_id.model not in self.env.registry.models:
                continue
            RecordModel = self.env[rule.model_id.model]
            if rule.active:
                for method in self._methods:
                    RecordModel._patch_method(method, audit_decorator(method))
                RecordModel.audit_rule = True
                updated = True
            if not rule.active:
                for method_name in self._methods:
                    method = getattr(RecordModel, method_name)
                    while hasattr(method, 'origin'):
                        if method.__name__ == 'audit_wrapper':
                            RecordModel._revert_method(method_name)
                            break
                        method = method.origin
                del RecordModel.audit_rule
                updated = True
        if updated:
            self.clear_caches()
        return updated

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        vals['state'] = 'done'
        rule = super(AuditRule, self).create(vals)
        rule.update_rule()
        if self._register_hook(rule.id):
            RegistryManager.signal_registry_change(self.env.cr.dbname)
        return rule

    @api.multi
    def write(self, vals):
        res = super(AuditRule, self).write(vals)
        self.update_rule()
        if self._register_hook(self._ids):
            RegistryManager.signal_registry_change(self.env.cr.dbname)
        return res

    @api.multi
    def unlink(self):
        self.update_rule(force_deactivation=True)
        return super(AuditRule, self).unlink()

    _ignored_fields = ['__last_update', 'message_ids', 'message_last_post']

    @classmethod
    def _format_data_to_log(cls, old_values, new_values):
        data = {}
        for age in ('old', 'new'):
            vals_list = old_values if age == 'old' else new_values
            if isinstance(vals_list, dict):
                vals_list = [vals_list]
            for vals in vals_list or []:
                for field in cls._ignored_fields:
                    vals.pop(field, None)
                res_id = vals.pop('id')
                if vals:
                    data.setdefault(res_id, {'old': {}, 'new': {}})[age] = vals
        for res_id in data.keys():
            for field in data[res_id]['old'].keys():
                if data[res_id]['old'][field] == data[res_id]['new'][field]:
                    del data[res_id]['old'][field]
                    del data[res_id]['new'][field]
            if data[res_id]['old'] == data[res_id]['new']:
                del data[res_id]
        return data

    @api.one
    def log(self, method, old_values=None, new_values=None):
        if old_values or new_values:
            data = self._format_data_to_log(old_values, new_values)
            AuditLog = self.env['audit.log'].sudo()
            for res_id in data:
                log = AuditLog.create({
                    'user_id': self._uid,
                    'model_id': self.sudo().model_id.id,
                    'res_id': res_id,
                    'method': method,
                    'data': data[res_id],
                })
        return True
