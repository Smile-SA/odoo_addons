# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp.osv import orm, fields
from openerp.tools.translate import _

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
    'REASSIGN', 'REFRESH', 'REINDEX', 'RELEASE', 'RESET', 'REVOKE',
    'ROLLBACK', 'SAVEPOINT', 'SECURITY', 'SET', 'SHOW', 'START',
    'TRUNCATE',
    'UNLISTEN', 'UPDATE',
    'VACUUM', 'VALUES',
]


_UNSAFE_KEYWORD_CONSTRAINT = ' AND '.join(
    ["NOT data_mask ~ '.*%s.*'" % kw for kw in _UNSAFE_SQL_KEYWORDS]
)


class IrModelFields(orm.Model):
    _inherit = 'ir.model.fields'

    _columns = {
        'data_mask': fields.char('Data mask'),
        'data_mask_locked': fields.boolean('Data mask locked')
    }
    _sql_constraints = [
        (
            'no_unsafe_keyword_data_mask',
            "CHECK("+_UNSAFE_KEYWORD_CONSTRAINT+")",
            _('You can not use an unsafe SQL keyword in a data mask')
        ),
        (
            'no_semicolumn_data_mask', "CHECK(NOT data_mask ~ '.*;.*')",
            _("You cannot use semicolumn character into a data mask")
        )
    ]

    def toggle_data_mask_locked(self, cr, uid, ids, context=None):

        new_data_mask = not self.browse(cr, uid, ids, context=None)[0].data_mask_locked
        cr.execute('update ir_model_fields set data_mask_locked=%s where id=%s', (new_data_mask, ids[0]))

    _safe_attributes = ['data_mask', 'data_mask_locked']

    def write(self, cr, uid, ids, vals, context=None):
        for attribute in self._safe_attributes:
            fields_to_update = self.search(cr, uid, [('id', 'in', ids), ('data_mask_locked', '=', False)], context=context)
            if attribute in vals:
                if fields_to_update:
                    value = vals[attribute] and vals[attribute] or ''
                    cr.execute('update ' + self._table + ' set ' + attribute + '=$$' + value + '$$ WHERE id IN %s',
                               (tuple(fields_to_update),))
                del vals[attribute]
        if not vals:
            return True
        return super(IrModelFields, self).write(cr, uid, ids, vals, context)

    def get_anonymization_query(self, cr, uid, context=None):
        field_ids = self.search(cr, uid, [('data_mask', '!=', None)], context=context)
        return self._get_anonymization_query(cr, uid, field_ids, context=context)

    def _get_anonymization_query(self, cr, uid, ids, context=None):
        query = "DELETE FROM ir_attachment WHERE name ilike '/web/content/%'" \
                "OR name ilike '%/static/%';\n"
        # query = ''
        data = {}
        for field in self.browse(cr, uid, ids, context=context):
            if field.model_id.model.replace('.', '_') not in data.keys():
                data[field.model_id.model.replace('.', '_')] = [
                    "UPDATE %s SET %s = %s" % (field.model_id.model.replace('.', '_'), field.name, field.data_mask)]
            else:
                if 'where'.lower() in field.data_mask.lower():
                    data[field.model_id.model.replace('.', '_')].append(
                        "UPDATE %s SET %s = %s" % (field.model_id.model.replace('.', '_'), field.name, field.data_mask))
                else:
                    data[field.model_id.model.replace('.', '_')][0] += ",%s = %s" % (field.name, field.data_mask)
        for val in data.values():
            query += ";\n".join(val) + ";\n"
        return query

