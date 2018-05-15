# -*- coding: utf-8 -*-

import logging
import sys

from odoo import api, fields, models, tools

_logger = logging.getLogger(__name__)

if sys.version_info > (3,):
    long = int

models.Model._old_id = True
native_auto_init = models.Model._auto_init
native_setup_base = models.Model._setup_base
native_load = models.Model.load


@api.model_cr_context
def _auto_init(self):
    name = 'old_id'
    if self._auto and self._old_id and name not in self._fields:
        field = fields.Integer(readonly=True)
        self._add_field(name, field)
    native_auto_init(self)


@api.model
def _setup_base(self):
    native_setup_base(self)
    name = 'old_id'
    if self._auto and self._old_id and name not in self._fields:
        field = fields.Integer(readonly=True)
        self._add_field(name, field)
        if tools.table_exists(self._cr, self._table):
            columns = tools.table_columns(self._cr, self._table)
            field.update_db_column(self, columns.get(name))


@api.model
def load(self, fields, data):
    if data:
        for index, field in enumerate(fields):
            if field in self._fields and \
                    self._fields[field].type == 'many2one' and \
                    isinstance(data[0][index], (int, long)):
                fields[index] = field + '.id'
    res = native_load(self, fields, data)
    for message in res['messages']:
        _logger.error(message)
    return res


models.Model._auto_init = _auto_init
models.Model._setup_base = _setup_base
models.Model.load = load
