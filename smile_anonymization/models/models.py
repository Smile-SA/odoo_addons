# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp import tools, api, fields, SUPERUSER_ID
from openerp.exceptions import except_orm
from openerp.models import Model, BaseModel
from openerp import osv

native_setup_fields = Model._setup_fields


@api.model
def _setup_fields(self):
    if self._name == 'ir.model.fields':
        self.env.cr.execute("""SELECT column_name FROM information_schema.columns
        WHERE table_name = 'ir_model_fields' and column_name in ('data_mask', 'data_mask_locked');
        """)
        if not self.env.cr.fetchall():
            self.env.cr.execute("""
                ALTER TABLE ir_model_fields
                ADD COLUMN data_mask VARCHAR,
                ADD COLUMN data_mask_locked BOOLEAN
                """
                                )
        self._add_field('data_mask', fields.Char())
        self._add_field('data_mask_locked', fields.Boolean())
    native_setup_fields(self)


def _new_field_create(self, cr, context=None):
    """ Create entries in ir_model_fields for all the model's fields.

    If necessary, also create an entry in ir_model, and if called from the
    modules loading scheme (by receiving 'module' in the context), also
    create entries in ir_model_data (for the model and the fields).

    - create an entry in ir_model (if there is not already one),
    - create an entry in ir_model_data (if there is not already one, and if
      'module' is in the context),
    - update ir_model_fields with the fields found in _columns
      (TODO there is some redundancy as _columns is updated from
      ir_model_fields in __init__).

    """
    if context is None:
        context = {}
    cr.execute("SELECT id FROM ir_model WHERE model=%s", (self._name,))
    if not cr.rowcount:
        cr.execute('SELECT nextval(%s)', ('ir_model_id_seq',))
        model_id = cr.fetchone()[0]
        cr.execute(
            "INSERT INTO ir_model (id,model, name, info,state) VALUES (%s, %s, %s, %s, %s)",
            (model_id, self._name, self._description, self.__doc__, 'base')
        )
    else:
        model_id = cr.fetchone()[0]
    if 'module' in context:
        name_id = 'model_' + self._name.replace('.', '_')
        cr.execute('select * from ir_model_data where name=%s and module=%s', (name_id, context['module']))
        if not cr.rowcount:
            cr.execute(
                "INSERT INTO ir_model_data (name,date_init,date_update,module,model,res_id) VALUES (%s, (now() at time zone 'UTC'), (now() at time zone 'UTC'), %s, %s, %s)", \
                (name_id, context['module'], 'ir.model', model_id)
                )

    cr.execute("SELECT * FROM ir_model_fields WHERE model=%s", (self._name,))
    cols = {}
    for rec in cr.dictfetchall():
        cols[rec['name']] = rec

    ir_model_fields_obj = self.pool.get('ir.model.fields')

    # sparse field should be created at the end, as it depends on its serialized field already existing
    model_fields = sorted(self._columns.items(), key=lambda x: 1 if x[1]._type == 'sparse' else 0)
    for (k, f) in model_fields:
        vals = {
            'model_id': model_id,
            'model': self._name,
            'name': k,
            'field_description': f.string,
            'ttype': f._type,
            'relation': f._obj or '',
            'select_level': tools.ustr(int(f.select)),
            'readonly': (f.readonly and 1) or 0,
            'required': (f.required and 1) or 0,
            'selectable': (f.selectable and 1) or 0,
            'translate': (f.translate and 1) or 0,
            'relation_field': f._fields_id if isinstance(f, osv.fields.one2many) else '',
            'serialization_field_id': None,
            'data_mask': getattr(f, 'data_mask', None),
            'data_mask_locked': getattr(f, 'data_mask_locked', False)
        }
        if getattr(f, 'serialization_field', None):
            # resolve link to serialization_field if specified by name
            serialization_field_id = ir_model_fields_obj.search(cr, SUPERUSER_ID,
                                                                [('model', '=', vals['model']), ('name', '=', f.serialization_field)])
            if not serialization_field_id:
                raise except_orm(_('Error'), _("Serialization field `%s` not found for sparse field `%s`!") % (f.serialization_field, k))
            vals['serialization_field_id'] = serialization_field_id[0]

        # When its a custom field,it does not contain f.select
        if context.get('field_state', 'base') == 'manual':
            if context.get('field_name', '') == k:
                vals['select_level'] = context.get('select', '0')
            # setting value to let the problem NOT occur next time
            elif k in cols:
                vals['select_level'] = cols[k]['select_level']

        if k not in cols:
            cr.execute('select nextval(%s)', ('ir_model_fields_id_seq',))
            id = cr.fetchone()[0]
            vals['id'] = id
            cr.execute("""INSERT INTO ir_model_fields (
                id, model_id, model, name, field_description, ttype,
                relation,state,select_level,relation_field, translate, serialization_field_id, data_mask, data_mask_locked
            ) VALUES (
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
            )""", (
                id, vals['model_id'], vals['model'], vals['name'], vals['field_description'], vals['ttype'],
                vals['relation'], 'base',
                vals['select_level'], vals['relation_field'], bool(vals['translate']), vals['serialization_field_id'],
                vals['data_mask'], vals['data_mask_locked']
            ))
            if 'module' in context:
                name1 = 'field_' + self._table + '_' + k
                cr.execute("select name from ir_model_data where name=%s", (name1,))
                if cr.fetchone():
                    name1 = name1 + "_" + str(id)
                cr.execute(
                    "INSERT INTO ir_model_data (name,date_init,date_update,module,model,res_id) VALUES (%s, (now() at time zone 'UTC'), (now() at time zone 'UTC'), %s, %s, %s)", \
                    (name1, context['module'], 'ir.model.fields', id)
                    )
        else:
            for key, val in vals.items():
                if cols[k][key] != vals[key]:
                    cr.execute('update ir_model_fields set field_description=%s where model=%s and name=%s',
                               (vals['field_description'], vals['model'], vals['name']))
                    cr.execute("""UPDATE ir_model_fields SET
                        model_id=%s, field_description=%s, ttype=%s, relation=%s,
                        select_level=%s, readonly=%s ,required=%s, selectable=%s, relation_field=%s, translate=%s, serialization_field_id=%s,
                        data_mask=%s, data_mask_locked=%s
                    WHERE
                        model=%s AND name=%s""", (
                        vals['model_id'], vals['field_description'], vals['ttype'],
                        vals['relation'],
                        vals['select_level'], bool(vals['readonly']), bool(vals['required']), bool(vals['selectable']), vals['relation_field'],
                        bool(vals['translate']), vals['serialization_field_id'], vals['data_mask'], vals['data_mask_locked'],
                        vals['model'], vals['name']
                    ))
                    break
    self.invalidate_cache(cr, SUPERUSER_ID)

Model._setup_fields = _setup_fields
BaseModel._field_create = _new_field_create