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

from audit_decorator import audit_decorator

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
    model_id = fields.Many2one('ir.model', 'Object', required=True,
                               help='Select object for which you want to generate log.',
                               domain=[('model', '!=', 'audit.log')],
                               readonly=True, states={'draft': [('readonly', False)]})
    action_id = fields.Many2one('ir.actions.act_window', 'Client Action', readonly=True)
    values_id = fields.Many2one('ir.values', "Add in the 'More' menu", readonly=True)

    _sql_constraints = [
        ('model_uniq', 'unique(model_id)', 'There is already a rule defined on this object.\n'
         'You cannot define another: please edit the existing one.'),
    ]

    @api.one
    def _add_action(self):
        if not self.action_id:
            vals = {
                'name': _('View audit logs'),
                'res_model': 'audit.log',
                'src_model': self.model_id.model,
                'domain': "[('model_id','=', %s), ('res_id', '=', active_id)]" % self.model_id.id,
            }
            self.action_id = self.env['ir.actions.act_window'].create(vals)

    @api.one
    def _add_values(self):
        if not self.values_id:
            self.env['ir.model.data'].ir_set('action', 'client_action_relate', 'view_log_' + self.model_id.model,
                                             [self.model_id.model], 'ir.actions.act_window,%s' % self.action_id.id,
                                             replace=True, isobject=True, xml_id=False)
            values = self.env['ir.values'].search([('model', '=', self.model_id.model),
                                                   ('value', '=', 'ir.actions.act_window,%s' % self.action_id.id)])
            if values:
                self.values_id = values[0]

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

    @tools.cache()
    def _check_audit_rule(self, cr):
        ids = self.search(cr, SUPERUSER_ID, [])
        return {rule.model_id.model:
                {method: rule.id
                 for method in ('create', 'write', 'unlink')
                 if getattr(rule, 'log_%s' % method)}
                for rule in self.browse(cr, SUPERUSER_ID, ids)}

    def _register_hook(self, cr, ids=None):
        updated = False
        if not ids:
            ids = self.search(cr, SUPERUSER_ID, [])
        for rule in self.browse(cr, SUPERUSER_ID, ids):
            model_obj = self.pool.get(rule.model_id.model)
            if not model_obj:
                continue
            if rule.active and not hasattr(model_obj, 'audit_rule'):
                for method in ('create', 'write', 'unlink'):
                    model_obj._patch_method(method, audit_decorator())
                model_obj.audit_rule = True
                updated = True
            if not rule.active and hasattr(model_obj, 'audit_rule'):
                for method_name in ('create', 'write', 'unlink'):
                    method = getattr(model_obj, method_name)
                    while hasattr(method, 'origin'):
                        if method.__name__ == 'audit_wrapper':
                            model_obj._revert_method(method_name)
                            break
                        method = method.origin
                del model_obj.audit_rule
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

    _ignored_fields = ['message_ids', 'message_last_post']

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
        return data

    @api.one
    def log(self, method, old_values=None, new_values=None):
        _logger.debug('Starting audit log')
        data = self._format_data_to_log(old_values, new_values)
        for res_id in data:
            self.env['audit.log'].sudo().create({
                'user_id': self._uid,
                'model_id': self.sudo().model_id.id,
                'method': method,
                'res_id': res_id,
                'data': repr(data[res_id]),
            })
        return True
