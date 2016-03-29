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

from openerp import api, models

native_read_from_database = models.BaseModel._read_from_database
native_fields_get = models.BaseModel.fields_get


@api.multi
def _read_from_database(self, field_names, inherited_field_names=[]):
    native_read_from_database(self, field_names, inherited_field_names=[])
    # Store history revision in cache
    if self._context.get('history_revision') and getattr(self._model, 'audit_rule', None):
        history_date = self._context.get('history_revision')
        create_rule = self.pool['audit.rule']._check_audit_rule(self._cr).get(self._name, {}).get('create')
        date_operator = create_rule and '>' or '>='
        domain = [('model', '=', self._name), ('res_id', 'in', self.ids),
                  ('create_date', date_operator, history_date)]
        logs = self.env['audit.log'].sudo().search(domain, order='create_date desc')
        for record in self:
            vals = {}
            for log in logs:
                if log.res_id == record.id:
                    data = eval(log.data or '{}')
                    vals.update(data.get('old', {}))
            if 'message_ids' in self._fields:
                vals['message_ids'] = record.message_ids.filtered(lambda msg: msg.date <= history_date)
            record._cache.update(record._convert_to_cache(vals, validate=False))


@api.cr_uid_context
def fields_get(self, cr, user, allfields=None, context=None, write_access=True, attributes=None):
    res = native_fields_get(self, cr, user, allfields, context, write_access, attributes)
    context = context or {}
    if context.get('history_revision'):
        for field in res:
            res[field]['readonly'] = True
    return res


models.BaseModel._read_from_database = _read_from_database
models.BaseModel.fields_get = fields_get
