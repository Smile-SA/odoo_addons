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
from openerp.models import BaseModel
from openerp.osv.expression import normalize_domain


_logger = logging.getLogger(__name__)

native_validate_fields = BaseModel._validate_fields
native_import_data = BaseModel.import_data
native_load = BaseModel.load
native_unlink = BaseModel.unlink


@api.multi
def new_validate_fields(self, fields_to_validate):
    if not self._context.get('no_validate'):
        native_validate_fields(self, fields_to_validate)


def new_load(self, cr, uid, fields, data, context=None):
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


def new_import_data(self, cr, uid, fields, datas, mode='init', current_module='', noupdate=False, context=None, filename=None):
    context_copy = context and context.copy() or {}
    context_copy['defer_parent_store_computation'] = True
    return native_import_data(self, cr, uid, fields, datas, mode, current_module, noupdate, context_copy, filename)


@api.multi
def new_unlink(self):
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


@api.model
@api.returns('self', lambda value: value.id)
def bulk_create(self, vals_list):
    if not vals_list:
        return []
    cr, uid, context = self.env.args
    context_copy = context and context.copy() or {}
    context_copy['no_validate'] = True
    context_copy['defer_parent_store_computation'] = True
    if not isinstance(vals_list, list):
        vals_list = [vals_list]
    records = self.browse()
    for vals in vals_list:
        records |= self.with_context(**context_copy).create(vals)
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

BaseModel.filtered_from_domain = filtered_from_domain
BaseModel._validate_fields = new_validate_fields
BaseModel.bulk_create = bulk_create
BaseModel.import_data = new_import_data
BaseModel.load = new_load
BaseModel.open_wizard = open_wizard
BaseModel.store_set_values = BaseModel._store_set_values
BaseModel._try_lock = _try_lock
BaseModel.unlink = new_unlink
