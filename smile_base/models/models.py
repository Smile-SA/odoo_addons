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

from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
from operator import and_, or_, sub
import psycopg2
import time

from openerp import api, _
from openerp.exceptions import Warning
from openerp.models import BaseModel
from openerp.osv.expression import normalize_domain


_logger = logging.getLogger(__name__)

native_validate_fields = BaseModel._validate_fields
native_import_data = BaseModel.import_data
native_load = BaseModel.load
native_unlink = BaseModel.unlink
native_store_get_values = BaseModel._store_get_values


@api.multi
def _validate_fields(self, fields_to_validate):
    if not self._context.get('no_validate'):
        native_validate_fields(self, fields_to_validate)


def load(self, cr, uid, fields, data, context=None):
    context_copy = context and context.copy() or {}
    context_copy['no_validate'] = True
    context_copy['defer_parent_store_computation'] = True
    res = native_load(self, cr, uid, fields, data, context_copy)
    ids = res['ids']
    if ids:
        recs = self.browse(cr, uid, ids, context)
        recs._validate_fields(fields)
        self._parent_store_compute(cr)
    return res


def import_data(self, cr, uid, fields, datas, mode='init', current_module='', noupdate=False, context=None, filename=None):
    context_copy = context and context.copy() or {}
    context_copy['defer_parent_store_computation'] = True
    return native_import_data(self, cr, uid, fields, datas, mode, current_module, noupdate, context_copy, filename)


@api.multi
def unlink(self):
    if hasattr(self.pool[self._name], '_cascade_relations'):
        self = self.with_context(active_test=False)
        if 'unlink_in_cascade' not in self._context:
            self = self.with_context(unlink_in_cascade={self._name: list(self._ids)})
        for model, fnames in self.pool[self._name]._cascade_relations.iteritems():
            domain = ['|'] * (len(fnames) - 1) + [(fname, 'in', self._ids) for fname in fnames]
            sub_model_obj = self.env[model]
            sub_models = sub_model_obj.search(domain)
            sub_model_ids = list(set(sub_models._ids) - set(self._context['unlink_in_cascade'].get(model, [])))
            if sub_model_ids:
                self._context['unlink_in_cascade'].setdefault(model, []).extend(sub_model_ids)
                sub_model_obj.browse(sub_model_ids).unlink()
    if not self.exists():
        return True
    return native_unlink(self)


@api.multi
def _store_get_values(self, fields):
    if self._context.get('no_store_function'):
        return []
    return native_store_get_values(fields)


@api.multi
def _compute_store_set(self):
    """
    Get the list of stored function fields to recompute (via _store_get_values)
    and recompute them (via _store_set_values)
    """
    store_get_result = self._store_get_values(self._columns.keys())
    store_get_result.sort()

    done = {}
    cr, uid, context = self.env.args
    for order, model, ids_to_update, fields_to_recompute in store_get_result:
        key = (model, tuple(fields_to_recompute))
        done.setdefault(key, {})
        # avoid to do several times the same computation
        ids_to_recompute = []
        for id_to_update in ids_to_update:
            if id_to_update not in done[key]:
                done[key][id_to_update] = True
                ids_to_recompute.append(id_to_update)
        self.pool[model]._store_set_values(cr, uid, ids_to_recompute, fields_to_recompute, context)


@api.model
@api.returns('self', lambda records: records.ids)
def bulk_create(self, vals_list):
    if not vals_list:
        return []
    context_copy = dict(self._context)
    if not self._context.get('force_store_function'):
        # 'force_store_function' useful if model has workflow with transition condition
        # based on function/compute fields
        context_copy['no_store_function'] = True
        context_copy['recompute'] = False
    context_copy['no_validate'] = True
    context_copy['defer_parent_store_computation'] = True
    if not isinstance(vals_list, list):
        vals_list = [vals_list]
    records = self.browse()
    for vals in vals_list:
        records |= self.with_context(**context_copy).create(vals)
    if not self._context.get('force_store_function'):
        records._compute_store_set()
        self.recompute()
    records._validate_fields(vals_list[0])
    self._parent_store_compute()
    return records


@api.multi
def _try_lock(self, warning=None):
    try:
        self._cr.execute("""SELECT id FROM "%s" WHERE id IN %%s FOR UPDATE NOWAIT""" % self._table,
                         (tuple(self.ids),), log_exceptions=False)
    except psycopg2.OperationalError:
        self._cr.rollback()  # INFO: Early rollback to allow translations to work for the user feedback
        if warning:
            raise Warning(warning)
        raise


@api.multi
def open_wizard(self, **kwargs):
    action = {
        'type': 'ir.actions.act_window',
        'res_model': self._name,
        'view_mode': 'form',
        'view_id': False,
        'res_id': self.ids and self.ids[0] or False,
        'domain': [],
        'target': 'new',
    }
    action.update(**kwargs)
    return action


@api.model
def _get_comparison_fields(self):
    return []


@api.multi
def _compare(self, other):
    """
    Compare an instance with another
    Return {field: (previous_value, new_value)}
    """
    self.ensure_one()
    other.ensure_one()
    diff = {}
    comparison_fields = self._get_comparison_fields()
    current_infos = self.read(comparison_fields)[0]
    other_infos = other.read(comparison_fields)[0]
    for field in comparison_fields:
        if current_infos[field] != other_infos[field]:
            diff[field] = (other_infos[field], current_infos[field])
    return diff


@api.multi
def _get_comparison_logs(self, other):

    def get_values(items):
        return map(lambda item: item[1], items)

    diff = self._compare(other)
    logs = []
    for field_name in diff:
        field = self._fields[field_name]
        label = field.string
        separator = ' -> '
        if field.type == 'many2one':
            diff[field_name] = get_values(diff[field_name])
        if field.type == 'one2many':
            diff[field_name] = get_values(self.env[field.comodel_name].browse(diff[field_name]).name_get())
            label = _('New %s') % label
            separator = ', '
        if field.type == 'selection':
            selection = dict(field.selection)
            diff[field_name] = [selection[key] for key in diff[field_name]]
        logs.append('<b>%s</b>: %s' % (label, separator.join(map(str, diff[field_name]))))
    return logs

SET_OPERATORS = {
    '&': and_,
    '|': or_,
    '!': sub,
}
SQL2PYTHON_OPERATORS = {
    '=': '==',
    '<>': '!=',
    'like': 'in',
    'ilike': 'in',
    'not like': 'not in',
    'not ilike': 'not in',
}


@api.multi
def filtered_from_domain(self, domain):
    if not domain or not self:
        return self

    localdict = {'time': time, 'datetime': datetime, 'relativedelta': relativedelta,
                 'context': self._context, 'uid': self._uid, 'user': self.env.user}
    try:
        if not isinstance(domain, basestring):
            domain = repr(domain)
        domain = normalize_domain(eval(domain, localdict))
    except:
        raise Warning(_('Domain not supported for %s filtering: %s') % (self._name, domain))

    stack = []

    def preformat(item):
        model = self[0]
        if item[0].split('.')[:-1]:
            model = eval('o.%s' % '.'.join(item[0].split('.')[:-1]), {'o': self[0]})
        field = model._fields[item[0].split('.')[-1]]
        if field.relational:
            if isinstance(item[2], basestring):
                item[2] = dict(self.env[field.comodel_name].name_search(name=item[2], operator=item[1])).keys()
                item[1] = 'in'
            if field.type.endswith('2many'):
                item[0] += '.ids'
            else:
                item[0] += '.id'
        return item

    def compute(item):
        item = preformat(item)
        if isinstance(item, tuple):
            item = list(item)
        item[0] = 'o.%s' % item[0]
        item[1] = SQL2PYTHON_OPERATORS.get(item[1], item[1])
        reverse = True if item[1] in ('in', 'not in') and not isinstance(item[2], (tuple, list)) else False
        item[2] = repr(item[2])
        if reverse:
            item = item[::-1]
        expr_to_eval = ' '.join(map(str, item))
        try:
            return self.filtered(lambda rec: eval(expr_to_eval, dict(localdict, o=rec)))
        except:
            return self.browse()

    def parse():
        for item in domain[::-1]:
            if isinstance(item, (tuple, list)):
                stack.append(compute(item))
            else:
                a = stack.pop()
                if item == '!':
                    b = self
                else:
                    b = stack.pop()
                stack.append(SET_OPERATORS[item](b, a))
        return stack.pop()

    return parse()


@api.multi
def recompute_fields(self, fnames):
    old_fnames = []
    for fname in fnames:
        field = self._fields[fname]
        if getattr(field.column, 'store', None):
            old_fnames.append(fname)
        elif getattr(field, 'store') and getattr(field, 'compute'):
            self._recompute_todo(field)
        else:
            raise Warning(_('%s is not a stored compute/function field') % fname)
    self._model._store_set_values(self._cr, self._uid, self.ids, old_fnames, self._context)
    self.recompute()
    return True


BaseModel.filtered_from_domain = filtered_from_domain
BaseModel._validate_fields = _validate_fields
BaseModel.bulk_create = bulk_create
BaseModel.import_data = import_data
BaseModel.load = load
BaseModel._get_comparison_fields = _get_comparison_fields
BaseModel._compare = _compare
BaseModel._get_comparison_logs = _get_comparison_logs
BaseModel.open_wizard = open_wizard
BaseModel._compute_store_set = _compute_store_set
BaseModel.recompute_fields = recompute_fields
BaseModel._try_lock = _try_lock
BaseModel.unlink = unlink
