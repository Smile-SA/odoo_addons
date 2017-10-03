# -*- coding: utf-8 -*-

from odoo import api, fields, models

models.Model._old_id = True
native_auto_init = models.Model._auto_init
native_call_kw_model = api.call_kw_model
native_call_kw_multi = api.call_kw_multi


@api.model_cr_context
def _auto_init(self):
    name = 'old_id'
    if self._auto and self._old_id and name not in self._fields:
        field = fields.Integer(index=True, readonly=True)
        self._add_field(name, field)
    native_auto_init(self)


def _convert_values(self, vals):
    for field in vals:
        if field in self._fields and \
                isinstance(self._fields[field], fields.Many2one) and \
                isinstance(vals[field], basestring):
            vals[field] = self.env['ir.model.data'].xmlid_to_res_id(
                vals[field], raise_if_not_found=True)


def call_kw_model(method, self, args, kwargs):
    if method.__name__ == 'create' and args:
        _convert_values(self, args[0])
    return native_call_kw_model(method, self, args, kwargs)


def call_kw_multi(method, self, args, kwargs):
    if args:
        args = list(args)
        old_ids = args[0] if hasattr(args[0], '__iter__') else [args[0]]
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
api.call_kw_model = call_kw_model
api.call_kw_multi = call_kw_multi
