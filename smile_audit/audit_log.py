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

import types

from openerp.osv import fields, orm
from openerp.tools.translate import _


class AuditLog(orm.Model):
    _name = 'audit.log'
    _description = 'Audit Log'
    _order = 'create_date desc'

    def _get_name(self, cr, uid, ids, name, arg, context=None):
        data = {}
        for log in self.browse(cr, uid, ids, context):
            if log.model_id and log.res_id:
                data[log.id] = dict(self.pool.get(log.model_id.model).name_get(cr, uid, [log.res_id], context))[log.res_id]
            else:
                data[log.id] = False
        return data

    _columns = {
        'name': fields.function(_get_name, method=True, type='char', size=256, string='Resource Name', store=True),
        'create_date': fields.datetime('Date', readonly=True),
        'user_id': fields.many2one('res.users', 'User', required=True, readonly=True),
        'model_id': fields.many2one('ir.model', 'Object', required=True, readonly=True),
        'method': fields.char('Method', size=64, readonly=True),
        'res_id': fields.integer('Resource Id', readonly=True),
        'line_ids': fields.one2many('audit.log.line', 'log_id', 'Log lines', readonly=True),
    }

    def create(self, cr, uid, vals, context=None):
        res_id = super(AuditLog, self).create(cr, uid, vals, context)
        self._store_set_values(cr, uid, [res_id], ['name'], context)
        return res_id

    def unlink(self, cr, uid, ids, context=None):
        raise orm.except_orm(_('Error'), _('You cannot remove audit logs!'))


class AuditLogLine(orm.Model):
    _name = 'audit.log.line'
    _description = 'Audit Log Line'
    _rec_name = 'field_name'

    def _get_fields_type(self, cr, uid, context=None):
        # Avoid too many nested `if`s below, as RedHat's Python 2.6
        # break on it. See bug 939653.
        return sorted([(k, k) for k, v in fields.__dict__.iteritems() if isinstance(v, types.TypeType) and issubclass(v, fields._column)
                       and v != fields._column and not v._deprecated and not issubclass(v, fields.function)])

    def _get_values(self, cr, uid, ids, name, arg, context=None):
        data = {}
        field_obj = self.pool.get('ir.model.fields')
        for line in self.browse(cr, uid, ids, context):
            old_value_text = line.old_value
            new_value_text = line.new_value
            field_ids = field_obj.search(cr, uid, [
                ('model_id', '=', line.log_id.model_id.id),
                ('name', '=', line.field_name),
            ], limit=1, context=context)
            field = None
            if field_ids:
                field = field_obj.browse(cr, uid, field_ids[0], context)
                if field.relation:
                    obj = self.pool.get(field.relation)
                    old_value = line.old_value and eval(line.old_value) or []
                    new_value = line.new_value and eval(line.new_value) or []
                    if field.ttype == 'many2one':
                        if old_value:
                            if isinstance(old_value, tuple):
                                old_value = old_value[0]
                            old_value_text = dict(obj.name_get(cr, uid, [old_value], context))[old_value]
                        if new_value:
                            if isinstance(new_value, tuple):
                                new_value = new_value[0]
                            new_value_text = dict(obj.name_get(cr, uid, [new_value], context))[new_value]
                    elif field.ttype in ('one2many', 'many2many'):
                        old_value_text = []
                        new_value_text = []
                        for id_ in old_value:
                            old_value_text.append(dict(obj.name_get(cr, uid, [id_], context))[id_])
                        for id_ in new_value:
                            new_value_text.append(dict(obj.name_get(cr, uid, [id_], context))[id_])
                        old_value_text = str(old_value_text)
                        new_value_text = str(new_value_text)
            data[line.id] = {
                'field_id': field and field.id or False,
                'field_description': field and field.field_description or 'Unknown',
                'field_type': field and field.ttype or 'char',
                'old_value_text': old_value_text,
                'new_value_text': new_value_text,
            }
        return data

    _columns = {
        'log_id': fields.many2one('audit.log', 'Log', required=True, readonly=True, ondelete='cascade'),
        'field_name': fields.char('Field name', size=64, required=True, readonly=True, select=True),
        'old_value': fields.text('Old Value', readonly=True),
        'new_value': fields.text('New Value', readonly=True),
        'old_value_text': fields.function(_get_values, method=True, type='text', string='Old value Text', store=True, multi='values'),
        'new_value_text': fields.function(_get_values, method=True, type='text', string='New value Text', store=True, multi='values'),
        'field_id': fields.function(_get_values, method=True, type='many2one', relation='ir.model.fields', string='Field', store=True,
                                    multi='values'),
        'field_description': fields.function(_get_values, method=True, type='char', size=256, string='Field label', store=True, multi='values'),
        'field_type': fields.function(_get_values, method=True, type='selection', selection=_get_fields_type, size=64, store=True, multi='values'),
    }

    def create(self, cr, uid, vals, context=None):
        res_id = super(AuditLogLine, self).create(cr, uid, vals, context)
        self._store_set_values(cr, uid, [res_id], ['old_value_text', 'new_value_text', 'field_id', 'field_description', 'field_type'], context)
        return res_id
