# -*- coding: utf-8 -*-
# (C) 2020 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import sys

from ast import literal_eval

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

if sys.version_info > (3,):
    long = int


class Base(models.AbstractModel):
    _inherit = 'base'

    dbId = fields.Integer(store=False)
    errorMessage = fields.Text(store=False)

    def _auto_init(self):
        name = 'old_id'
        if self._auto and name not in self._fields:
            field = fields.Integer(readonly=True)
            self._add_field(name, field)
        super()._auto_init()

    @api.model
    def _setup_base(self):
        super()._setup_base()
        name = 'old_id'
        if self._auto and name not in self._fields:
            field = fields.Integer(readonly=True)
            self._add_field(name, field)
            if tools.table_exists(self._cr, self._table):
                columns = tools.table_columns(self._cr, self._table)
                field.update_db_column(self, columns.get(name))

    @api.model
    def load(self, fields, data):
        if data:
            for index, field in enumerate(fields):
                if field.endswith('__id'):
                    fields[index] = field.replace('__id', ':id')
                if field in self._fields and \
                        self._fields[field].type == 'many2one' and \
                        isinstance(data[0][index], (int, long)):
                    fields[index] = field + '.id'
                if field == 'errorMessage':
                    del fields[index]
                    del data[0][index]
        res = super(Base, self).load(fields, data)
        if res['messages']:
            for message in res['messages']:
                _logger.error(message)
            if self._context.get('raise_load_exceptions'):
                raise UserError('\n'.join(map(str, res['messages'])))
        return res

    @api.model
    def load_strings(self, str_fields, str_data, separator):
        fields = [literal_eval(field) for field in str_fields.split(separator)]
        data = [literal_eval(field) for field in str_data.split(separator)]
        return self.load(fields, [data])

    @api.model
    def load_strings_bulk(
            self, str_fields, str_data, separator, data_separator):
        fields = [literal_eval(field) for field in str_fields.split(separator)]
        data = [[literal_eval(field) for field in
                 second_data.split(separator)] for second_data
                in [first_data for first_data
                    in str_data.split(data_separator)]]
        return self.load(fields, data)

    @api.model
    def read_strings(self, str_fields, separator, str_domain="[]"):
        fields = [literal_eval(field) for field in str_fields.split(separator)]
        return self.search_read(literal_eval(str_domain), fields)

    @api.model
    def _update_insert_values(self, field, value, vals, m2o_fields, m2o_relations,  m2m_fields, m2m_relations):
        if hasattr(self, field):
            if field in m2m_fields:
                model = m2m_relations[m2m_fields.index(field)]
                record_ids = [(6, 0, [int(idx) for idx in eval(value)
                                      if self.env[model].search([('id', '=', int(idx))])])]
                vals.update({field: record_ids})
            elif field in m2o_fields:
                model = m2o_relations[m2o_fields.index(field)]
                vals.update({field: self.env[model].search([('id', '=', int(value))]).id})
            elif self._fields[field].type == 'boolean':
                lower_value = value.lower()
                if lower_value in ['true', '1']:
                    vals.update({field: True})
                elif lower_value in ['false', '0']:
                    vals.update({field: False})
            else:
                vals.update({field: value})

    @api.model
    def insert_string(self, separator, str_fields, str_values):
        vals = {}
        fields = [literal_eval(field) for field in str_fields.split(separator)]
        data = [literal_eval(val) for val in str_values.split(separator)]
        # Check unknown fields
        unknown_fields = set(fields).difference(self._fields.keys())
        if unknown_fields:
            raise UserError(
                _('{} field(s) unknown.').format(','.join(unknown_fields)))
        if fields and data and len(fields) == len(data):
            m2o_fields = [field.name for fieldname, field in self._fields.items()
                          if field.type == 'many2one']
            m2o_relations = [field.comodel_name for fieldname, field in self._fields.items()
                             if field.type == 'many2one']
            m2m_fields = [field.name for fieldname, field in self._fields.items()
                          if field.type == 'many2many']
            m2m_relations = [field.comodel_name for fieldname, field in self._fields.items()
                             if field.type == 'many2many']
            for index, field in enumerate(fields):
                self._update_insert_values(field, data[index], vals, m2o_fields,
                                           m2o_relations, m2m_fields, m2m_relations)
        if not vals:
            raise UserError(_('Something wrong with values or fields!'))
        return self.create(vals).id

    @api.model
    def update_string(self, record_id, separator, str_fields, str_values):
        vals = {}
        fields = [literal_eval(field) for field in str_fields.split(separator)]
        data = [literal_eval(val) for val in str_values.split(separator)]
        # Check unknown fields
        unknown_fields = set(fields).difference(self._fields.keys())
        if unknown_fields:
            raise UserError(
                _('{} field(s) unknown.').format(','.join(unknown_fields)))
        if not record_id:
            raise UserError(_('ID is not set!'))
        record = self.browse(int(record_id))
        if not record:
            raise UserError(_('This record not exist!'))
        if fields and data and len(fields) == len(data):
            m2o_fields = [field.name for fieldname, field in self._fields.items() if field.type == 'many2one']
            m2o_relations = [field.comodel_name for fieldname, field in self._fields.items() if
                             field.type == 'many2one']
            m2m_fields = [field.name for fieldname, field in self._fields.items()
                          if field.type == 'many2many']
            m2m_relations = [field.comodel_name for fieldname, field in self._fields.items()
                             if field.type == 'many2many']
            for index, field in enumerate(fields):
                self._update_insert_values(
                    field, data[index], vals, m2o_fields, m2o_relations,
                    m2m_fields, m2m_relations)
        if not vals:
            raise UserError(_('Something wrong with values or fields!'))
        record.write(vals)
        return record.id
