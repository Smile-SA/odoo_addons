from openerp import tools, api, fields, SUPERUSER_ID, _
from openerp.exceptions import except_orm, UserError
from openerp.models import Model, BaseModel
from openerp import osv

native_setup_fields = Model._setup_fields


@api.model
def _setup_fields(self, partial):
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
    native_setup_fields(self, partial)


def new_field_create(self, cr, context=None):
        if context is None:
            context = {}
        cr.execute("""
            UPDATE ir_model
               SET transient=%s
             WHERE model=%s
         RETURNING id
        """, [self._transient, self._name])
        if not cr.rowcount:
            cr.execute('SELECT nextval(%s)', ('ir_model_id_seq',))
            model_id = cr.fetchone()[0]
            cr.execute("INSERT INTO ir_model (id, model, name, info, state, transient) VALUES (%s, %s, %s, %s, %s, %s)",
                       (model_id, self._name, self._description, self.__doc__, 'base', self._transient))
        else:
            model_id = cr.fetchone()[0]
        if 'module' in context:
            name_id = 'model_'+self._name.replace('.', '_')
            cr.execute('select * from ir_model_data where name=%s and module=%s', (name_id, context['module']))
            if not cr.rowcount:
                cr.execute("INSERT INTO ir_model_data (name,date_init,date_update,module,model,res_id) VALUES"
                           " (%s, (now() at time zone 'UTC'), (now() at time zone 'UTC'), %s, %s, %s)",
                           (name_id, context['module'], 'ir.model', model_id)
                           )

        cr.execute("SELECT * FROM ir_model_fields WHERE model=%s", (self._name,))
        cols = {}
        for rec in cr.dictfetchall():
            cols[rec['name']] = rec

        ir_model_fields_obj = self.pool.get('ir.model.fields')

        # sparse field should be created at the end, as it depends on its serialized field already existing
        model_fields = sorted(self._fields.items(), key=lambda x: 1 if x[1].type == 'sparse' else 0)
        for (k, f) in model_fields:
            vals = {
                'model_id': model_id,
                'model': self._name,
                'name': k,
                'field_description': f.string,
                'help': f.help or None,
                'ttype': f.type,
                'relation': f.comodel_name or None,
                'index': bool(f.index),
                'copy': bool(f.copy),
                'related': f.related and ".".join(f.related),
                'readonly': bool(f.readonly),
                'required': bool(f.required),
                'selectable': bool(f.search or f.store),
                'translate': bool(getattr(f, 'translate', False)),
                'relation_field': f.type == 'one2many' and f.inverse_name or None,
                'serialization_field_id': None,
                'relation_table': f.type == 'many2many' and f.relation or None,
                'column1': f.type == 'many2many' and f.column1 or None,
                'column2': f.type == 'many2many' and f.column2 or None,
                'data_mask': getattr(f, 'data_mask', None),
                'data_mask_locked': getattr(f, 'data_mask_locked', False)
            }
            if getattr(f, 'serialization_field', None):
                # resolve link to serialization_field if specified by name
                serialization_field_id = ir_model_fields_obj.search(cr, SUPERUSER_ID,
                                                                    [('model', '=', vals['model']),
                                                                     ('name', '=', f.serialization_field)])
                if not serialization_field_id:
                    raise UserError(_("Serialization field `%s` not found for sparse field `%s`!") % (f.serialization_field, k))
                vals['serialization_field_id'] = serialization_field_id[0]

            if k not in cols:
                cr.execute('select nextval(%s)', ('ir_model_fields_id_seq',))
                id = cr.fetchone()[0]
                vals['id'] = id
                query = "INSERT INTO ir_model_fields (%s) VALUES (%s)" % (
                    ",".join(vals),
                    ",".join("%%(%s)s" % name for name in vals),
                )
                cr.execute(query, vals)
                if 'module' in context:
                    name1 = 'field_' + self._table + '_' + k
                    cr.execute("select name from ir_model_data where name=%s", (name1,))
                    if cr.fetchone():
                        name1 = name1 + "_" + str(id)
                    cr.execute("INSERT INTO ir_model_data (name,date_init,date_update,module,model,res_id) VALUES "
                               "(%s, (now() at time zone 'UTC'), (now() at time zone 'UTC'), %s, %s, %s)",
                               (name1, context['module'], 'ir.model.fields', id)
                               )
            else:
                for key, val in vals.items():
                    if cols[k][key] != vals[key]:
                        names = set(vals) - set(['model', 'name'])
                        query = "UPDATE ir_model_fields SET %s WHERE model=%%(model)s and name=%%(name)s" % (
                            ",".join("%s=%%(%s)s" % (name, name) for name in names),
                        )
                        cr.execute(query, vals)
                        break
        self.invalidate_cache(cr, SUPERUSER_ID)


Model._setup_fields = _setup_fields
BaseModel._field_create = new_field_create
