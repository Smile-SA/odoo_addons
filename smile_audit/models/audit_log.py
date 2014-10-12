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

import re

from openerp import api, fields, models, _
from openerp.exceptions import Warning


class AuditLog(models.Model):
    _name = 'audit.log'
    _description = 'Audit Log'
    _order = 'create_date desc'

    @api.one
    @api.depends('model_id', 'res_id')
    def _get_name(self):
        if self.model_id and self.res_id:
            res = self.env[self.model_id.model].browse(self.res_id).exists()
            if res:
                self.name = res.display_name
        else:
            self.name = ''

    name = fields.Char('Resource Name', size=256, compute='_get_name', store=True)
    create_date = fields.Datetime('Date', readonly=True)
    user_id = fields.Many2one('res.users', 'User', required=True, readonly=True)
    model_id = fields.Many2one('ir.model', 'Object', required=True, readonly=True)
    res_id = fields.Integer('Resource Id', readonly=True)
    method = fields.Char('Method', size=64, readonly=True)
    line_ids = fields.One2many('audit.log.line', 'log_id', 'Log lines', readonly=True)

    @api.multi
    def unlink(self):
        raise Warning(_('You cannot remove audit logs!'))


class AuditLogLine(models.Model):
    _name = 'audit.log.line'
    _description = 'Audit Log Line'
    _rec_name = 'field_name'

    @api.one
    def _get_values(self):
        res_users_pattern = re.compile(r'(^(in_group_|sel_groups_))(\d+)')
        old_value_text = self.old_value
        new_value_text = self.new_value
        all_models = [self.log_id.model_id.model]
        all_models += self.env[self.log_id.model_id.model]._inherits.keys()  # TODO: make recursive
        field = self.env['ir.model.fields'].sudo().search([('model_id.model', 'in', all_models), ('name', '=', self.field_name)], limit=1)
        if not field:
            self.field_id = self.field_type = self.field_description = self.old_value_text = self.new_value_text = False
            if res_users_pattern.match(self.field_name) \
                    or self.new_value or self.old_value:  # Treat res users special fields
                self.field_description = self.field_name
                self.old_value_text = old_value_text
                self.new_value_text = new_value_text
            return
        field = field[0]
        self.field_id = field
        self.field_type = field.ttype.capitalize()
        self.field_description = field.field_description
        if field.relation:
            obj = self.env[field.relation]
            old_value = self.old_value and eval(self.old_value) or []
            new_value = self.new_value and eval(self.new_value) or []
            if field.ttype == 'many2one':
                if old_value:
                    if isinstance(old_value, tuple):
                        old_value = old_value[0]
                    old = obj.browse(old_value).exists()
                    old_value_text = old and old.display_name or old_value
                if new_value:
                    if isinstance(new_value, tuple):
                        new_value = new_value[0]
                    new_value_text = obj.browse(new_value).display_name
            elif field.ttype in ('one2many', 'many2many'):
                if old_value:
                    old_value_text = []
                    for old_v in old_value:
                        old = obj.browse(old_v).exists()
                        old_value_text.append(old.display_name if old else str(old_v))
                    old_value_text = ', '.join(old_value_text)
                if new_value:
                    new_value_text = ', '.join([o.display_name for o in obj.browse(new_value)])
        self.old_value_text = old_value_text
        self.new_value_text = new_value_text

    log_id = fields.Many2one('audit.log', 'Log', required=True, readonly=True, ondelete='cascade')
    field_name = fields.Char('Field name', size=64, required=True, readonly=True, select=True)
    old_value = fields.Text('Old Value', readonly=True)
    new_value = fields.Text('New Value', readonly=True)
    old_value_text = fields.Text('Old value (text)', compute='_get_values')
    new_value_text = fields.Text('New value (text)', compute='_get_values')
    field_id = fields.Many2one('ir.model.fields', 'Field', compute='_get_values')
    field_description = fields.Char('Field label', size=256, compute='_get_values')
    field_type = fields.Char('Field type', size=64, compute='_get_values')
