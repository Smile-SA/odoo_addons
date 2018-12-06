# -*- coding: utf-8 -*-

import logging
import sys

from odoo import api, fields, models, tools
from odoo.exceptions import UserError
from .. import tools

models.Model._old_id = True

native_auto_init = models.Model._auto_init
native_setup_base = models.Model._setup_base
native_setup_load = models.Model.load
native_call_kw_model = api.call_kw_model
native_call_kw_multi = api.call_kw_multi

_logger = logging.getLogger(__name__)

if sys.version_info > (3,):
    long = int


@api.model_cr_context
def _auto_init(self):
    name = 'old_id'
    if self._auto and name not in self._fields:
        field = fields.Integer(readonly=True)
        self._add_field(name, field)
    native_auto_init(self)


@api.model
def _setup_base(self, partial):
    native_setup_base(self, partial)
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
    res = native_setup_load(self, fields, data)
    if res['messages']:
        for message in res['messages']:
            _logger.error(message)
        if self._context.get('raise_load_exceptions'):
            raise UserError('\n'.join(map(str, res['messages'])))
    return res


def _convert_values(self, vals):
    for field in vals:
        if field in self._fields and \
                isinstance(self._fields[field], fields.Many2one) and \
                isinstance(vals[field], basestring):
            vals[field] = self.env['ir.model.data'].xmlid_to_res_id(
                vals[field], raise_if_not_found=True)


def _convert_domain(self, domain):
    for index, condition in enumerate(domain):
        if isinstance(condition, (tuple, list)) and condition[2] and \
                (isinstance(condition[2], basestring) or
                 (isinstance(condition[2], list) and
                  isinstance(condition[2][0], basestring))):
            if isinstance(condition, tuple):
                condition = list(condition)
            model = self
            for field_name in condition[0].split('.'):
                field = model._fields.get(field_name)
                relational_types = (fields.Many2one,
                                    fields.One2many, fields.Many2many)
                if isinstance(field, relational_types):
                    model = self.env[field.comodel_name]
                elif field_name != 'id':
                    break
            else:
                IrModelData = self.env['ir.model.data']
                if isinstance(condition[2], basestring):
                    condition[2] = IrModelData.xmlid_to_res_id(
                        condition[2], raise_if_not_found=True)
                else:
                    ids = []
                    for xmlid in condition[2]:
                        ids.append(IrModelData.xmlid_to_res_id(
                            xmlid, raise_if_not_found=True))
                    condition[2] = ids
            domain[index] = condition


def call_kw_model(method, self, args, kwargs):
    if method.__name__ in ['create', 'checklist_wrapper'] and args:
        _convert_values(self, args[0])
    if method.__name__ in ('search', 'search_read', 'search_count') and args:
        _convert_domain(self, args[0])
    return native_call_kw_model(method, self, args, kwargs)


def call_kw_multi(method, self, args, kwargs):
    if args:
        args = list(args)
        old_ids = args[0]
        if not isinstance(args[0], (list, tuple, set)):
            old_ids = [args[0]]
        new_ids = []
        for id_ in old_ids:
            if isinstance(id_, basestring):
                new_ids.append(self.env['ir.model.data'].xmlid_to_res_id(
                    id_, raise_if_not_found=True))
            else:
                new_ids.append(id_)
        args[0] = new_ids if hasattr(args[0], '__iter__') else new_ids[0]
        if method.__name__ == 'write' and len(args) > 1:
            _convert_values(self, args[1])
        args = tuple(args)
    return native_call_kw_multi(method, self, args, kwargs)


models.Model._auto_init = _auto_init
models.Model._setup_base = _setup_base
models.Model.load = load
api.call_kw_model = call_kw_model
api.call_kw_multi = call_kw_multi
