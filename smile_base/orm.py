# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp.osv.orm import BaseModel

native_import_data = BaseModel.import_data
native_unlink = BaseModel.unlink
native_validate = BaseModel._validate


def new_validate(self, cr, uid, ids, context=None):
    context = context or {}
    if context.get('no_validate'):
        return
    native_validate(self, cr, uid, ids, context)


# Helper function combining _store_get_values and _store_set_values
def _compute_store_set(self, cr, uid, ids, context):
    """
    Get the list of stored function field to recompute (via _store_get_values)
    and recompute them (via _store_set_values)
    """
    store_get_result = self._store_get_values(cr, uid, ids, self._columns.keys(), context)
    store_get_result.sort()

    done = {}
    for order, model, ids_to_update, fields_to_recompute in store_get_result:
        key = (model, tuple(fields_to_recompute))
        done.setdefault(key, {})
        # avoid to do several times the same computation
        todo = []
        for id_to_update in ids_to_update:
            if id_to_update not in done[key]:
                done[key][id_to_update] = True
                todo.append(id_to_update)
        self.pool.get(model)._store_set_values(cr, uid, todo, fields_to_recompute, context)


def new_import_data(self, cr, uid, fields, datas, mode='init', current_module='', noupdate=False, context=None, filename=None):
    context_copy = context and context.copy() or {}
    context_copy['defer_parent_store_computation'] = True
    return native_import_data(self, cr, uid, fields, datas, mode, current_module, noupdate, context_copy, filename)


def new_unlink(self, cr, uid, ids, context=None):
    """Force unlink for remote fields.many2one with ondelete='cascade'"""
    if hasattr(self, '_cascade_relations'):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for model, fnames in self._cascade_relations.iteritems():
            domain = ['|'] * (len(fnames) - 1) + [(fname, 'in', ids) for fname in fnames]
            sub_model_obj = self.pool.get(model)
            sub_model_ids = sub_model_obj.search(cr, uid, domain, context=context)
            sub_model_obj.unlink(cr, uid, sub_model_ids, context)
    return native_unlink(self, cr, uid, ids, context)


def bulk_create(self, cr, uid, vals_list, context=None):
    context_copy = context and context.copy() or {}
    context_copy['no_store_function'] = True
    context_copy['no_validate'] = True
    context_copy['defer_parent_store_computation'] = True
    ids = []
    if not isinstance(vals_list, list):
        vals_list = [vals_list]
    for vals in vals_list:
        ids.append(self.create(cr, uid, vals, context_copy))
    self._compute_store_set(cr, uid, ids, context)
    self._validate(cr, uid, ids, context)
    self._parent_store_compute(cr)
    return True

BaseModel._compute_store_set = _compute_store_set
BaseModel._validate = new_validate
BaseModel.bulk_create = bulk_create
BaseModel.import_data = new_import_data
BaseModel.store_set_values = BaseModel._store_set_values
BaseModel.unlink = new_unlink
