# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

# PostgreSQL commands list
_UNSAFE_SQL_KEYWORDS = [
    'ABORT', 'ALTER',
    'BEGIN',
    'CALL', 'CHECKPOINT', 'CLOSE', 'CLUSTER', 'COMMIT', 'COPY', 'CREATE',
    'DEALLOCATE', 'DECLARE', 'DELETE', 'DISCARD', 'DO', 'DROP',
    'END', 'EXECUTE', 'EXPLAIN',
    'FETCH',
    'GRANT',
    'IMPORT', 'INSERT',
    'LISTEN', 'LOAD', 'LOCK',
    'MOVE',
    'PREPARE',
    'REASSIGN', 'REFRESH', 'REINDEX', 'RELEASE', 'RESET', 'REVOKE', 'ROLLBACK',
    'SAVEPOINT', 'SECURITY', 'SET', 'SHOW', 'START',
    'TRUNCATE',
    'UNLISTEN', 'UPDATE',
    'VACUUM', 'VALUES',
]


class IrModelFields(models.Model):
    _inherit = 'ir.model.fields'

    data_mask = fields.Char()
    data_mask_locked = fields.Boolean()

    @api.one
    @api.constrains('data_mask')
    def _check_data_mask(self):

        def _format(string):
            return " %s " % string.lower()

        if self.data_mask:
            if ';' in self.data_mask:
                raise ValidationError(
                    _("You cannot use ';' character into a data mask"))
            for unsafe_keyword in _UNSAFE_SQL_KEYWORDS:
                if _format(unsafe_keyword) in _format(self.data_mask):
                    raise ValidationError(
                        _("You cannot use '%s' keyword into a data mask")
                        % unsafe_keyword)

    def _reflect_field_params(self, field):
        vals = super(IrModelFields, self)._reflect_field_params(field)
        vals['data_mask'] = getattr(field, 'data_mask', None)
        return vals

    def _instanciate_attrs(self, field_data):
        attrs = super(IrModelFields, self)._instanciate_attrs(field_data)
        if attrs and field_data.get('data_mask'):
            attrs['data_mask'] = field_data['data_mask']
        return attrs

    @api.one
    def toggle_data_mask_locked(self):
        self.data_mask_locked = not self.data_mask_locked

    _safe_attributes = ['data_mask', 'data_mask_locked']

    @api.multi
    def write(self, vals):
        for attribute in self._safe_attributes:
            if attribute in vals:
                fields_to_update = self
                if attribute == 'data_mask':
                    fields_to_update = self.filtered(
                        lambda field: not field.data_mask_locked)
                fields_to_update._write({attribute: vals[attribute]})
                del vals[attribute]
        return super(IrModelFields, self).write(vals)

    @api.model
    def get_anonymization_query(self):
        return self.search([
            ('data_mask', '!=', False),
            ('store', '=', True),
        ])._get_anonymization_query()

    @api.multi
    def _get_anonymization_query(self):
        query = "DELETE FROM ir_attachment WHERE name ilike '/web/content/%'" \
                "OR name ilike '%/static/%';\n"
        data = {}
        for field in self:
            if field.data_mask:
                if self.env[field.model]._table not in data.keys():
                    data[self.env[field.model]._table] = [
                        "UPDATE %s SET %s = %s" % (self.env[field.model]._table, field.name, field.data_mask)]
                else:
                    if 'where'.lower() in field.data_mask.lower():
                        data[self.env[field.model]._table].append(
                            "UPDATE %s SET %s = %s" % (self.env[field.model]._table, field.name, field.data_mask))
                    else:
                        data[self.env[field.model]._table][0] += ",%s = %s" % (field.name, field.data_mask)
        for val in data.values():
            query += ";\n".join(val) + ";\n"
        return query
