# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _

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
_UNSAFE_KEYWORD_CONSTRAINT = ' AND '.join(
    ["NOT data_mask ~ '.*%s.*'" % kw for kw in _UNSAFE_SQL_KEYWORDS]
)


class IrModelFields(models.Model):
    _inherit = 'ir.model.fields'

    _sql_constraints = [
        (
            'no_unsafe_keyword_data_mask',
            "CHECK(" + _UNSAFE_KEYWORD_CONSTRAINT + ")",
            _('You can not use an unsafe SQL keyword in a data mask')
        ),
        (
            'no_semicolumn_data_mask', "CHECK(NOT data_mask ~ '.*;.*')",
            _("You cannot use semicolumn character into a data mask")
        )
    ]

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
        return self.search([('data_mask', '!=', False), ])._get_anonymization_query()

    @api.multi
    def _get_anonymization_query(self):
        query = "DELETE FROM ir_attachment WHERE name ilike '/web/content/%'" \
                "OR name ilike '%/static/%';\n"
        for field in self:
            if field.data_mask and not field.related:
                query += "UPDATE %s SET %s = %s;\n" % (
                    self.env[field.model]._table, field.name, field.data_mask)
        return query
