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

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging
from operator import and_, or_, sub
import psycopg2
import pytz
from six import string_types
import time

from odoo import api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.models import BaseModel
from odoo.osv.expression import normalize_domain
from odoo.tools.safe_eval import safe_eval


_logger = logging.getLogger(__name__)

native_load = BaseModel.load
native_modified = BaseModel.modified
native_read_group_process_groupby = BaseModel._read_group_process_groupby
native_unlink = BaseModel.unlink
native_validate_fields = BaseModel._validate_fields


@api.multi
def _validate_fields(self, fields_to_validate):
    if not self._context.get('no_validate'):
        try:
            native_validate_fields(self, fields_to_validate)
        except ValidationError as e:
            name = e.name.replace("%s\n\n" % _("Error while validating constraint"), "").replace("\nNone", "")
            raise ValidationError(name)


@api.model
def load(self, fields, data):
    self = self.with_context(no_validate=True, defer_parent_store_computation=True)
    res = native_load(self, fields, data)
    ids = res['ids']
    if ids:
        recs = self.browse(ids)
        recs._validate_fields(fields)
        self._parent_store_compute()
    return res


@api.multi
def unlink(self):
    if hasattr(self.pool[self._name], '_cascade_relations'):
        self = self.with_context(active_test=False)
        if 'unlink_in_cascade' not in self._context:
            self = self.with_context(unlink_in_cascade={self._name: list(self._ids)})
        for model, fnames in self.pool[self._name]._cascade_relations.items():
            domain = ['|'] * (len(fnames) - 1) + [(fname, 'in', self._ids) for fname in fnames]
            SubModel = self.env[model]
            sub_models = SubModel.search(domain)
            sub_model_ids = list(set(sub_models._ids) - set(self._context['unlink_in_cascade'].get(model, [])))
            if sub_model_ids:
                self._context['unlink_in_cascade'].setdefault(model, []).extend(sub_model_ids)
                SubModel.browse(sub_model_ids).unlink()
    if not self.exists():
        return True
    return native_unlink(self)


@api.multi
def modified(self, fnames):
    if self._context.get('recompute', True):
        native_modified(self, fnames)


@api.model
@api.returns('self', lambda records: records.ids)
def bulk_create(self, vals_list):
    if not vals_list:
        return self.browse()
    context = dict(self._context)
    if not self._context.get('force_store_function'):
        # 'force_store_function' useful if model has workflow with transition condition
        # based on function/compute fields
        context['no_store_function'] = True
        context['recompute'] = False
    context['no_validate'] = True
    context['defer_parent_store_computation'] = True
    if not isinstance(vals_list, list):
        vals_list = [vals_list]
    records = self.browse()
    for vals in vals_list:
        records |= self.with_context(**context).create(vals)
    if not self._context.get('force_store_function'):
        records.modified(self._fields)
        self.recompute()
    self._parent_store_compute()
    records._validate_fields(vals_list[0])
    return records


@api.multi
def _try_lock(self, warning=None):
    try:
        self._cr.execute("""SELECT id FROM "%s" WHERE id IN %%s FOR UPDATE NOWAIT""" % self._table,
                         (tuple(self.ids),), log_exceptions=False)
    except psycopg2.OperationalError:
        self._cr.rollback()  # INFO: Early rollback to allow translations to work for the user feedback
        if warning:
            raise UserError(warning)
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
        return map(lambda item: item and item[1], items)

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
        log = separator.join(map(tools.ustr, diff[field_name]))
        logs.append('<b>%s</b>: %s' % (label, log))
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
    if isinstance(domain, string_types):
        domain = safe_eval(domain)
    if not domain or not self:
        return self

    def get_records(item):
        records = self
        remote_field = item[0].split('.')[:-1]
        if remote_field:
            records = eval("rec.mapped('%s')" % '.'.join(remote_field), {'rec': self})
        return records

    def get_field(item):
        return get_records(item)._fields[item[0].split('.')[-1]]

    def extend(domain):
        for index, item in enumerate(domain):
            if isinstance(item, list):
                field = get_field(item)
                if field.search and not field.related:
                    extension = field.search(get_records(item), *item[1:])
                    domain = domain[:index] + normalize_domain(extension) + domain[index + 1:]
        return domain

    localdict = {'time': time, 'datetime': datetime, 'relativedelta': relativedelta,
                 'context': self._context, 'uid': self._uid, 'user': self.env.user}
    try:
        if not isinstance(domain, string_types):
            domain = repr(domain)
        domain = extend(normalize_domain(eval(domain, localdict)))
    except Exception:
        raise UserError(_('Domain not supported for %s filtering: %s') % (self._name, domain))

    stack = []

    def preformat(item):
        if isinstance(item, tuple):
            item = list(item)
        reverse = False
        field = get_field(item)
        if field.relational:
            if isinstance(item[2], string_types):
                item[2] = dict(self.env[field.comodel_name].name_search(name=item[2], operator=item[1], limit=0)).keys()
                item[1] = 'in'
            item[0] = 'rec.%s' % item[0]
            if field.type.endswith('2many'):
                item[0] += '.ids'
                py_operator = SQL2PYTHON_OPERATORS.get(item[1], item[1])
                if py_operator in ('in', 'not in'):
                    item[0] = '%sset(%s)' % (py_operator.startswith('not') and 'not ' or '', item[0])
                    item[1] = '&'
                    item[2] = set(item[2])
            else:
                item[0] += '.id'
        else:
            reverse = 'like' in item[1]
            item[0] = 'rec.%s' % item[0]
        item[1] = SQL2PYTHON_OPERATORS.get(item[1], item[1])
        item[2] = repr(item[2])
        if reverse:
            item = item[::-1]
        return ' '.join(map(str, item))

    def compute(item):
        try:
            expr = preformat(item)
            return self.filtered(lambda rec: eval(expr, dict(localdict, rec=rec)))
        except Exception:
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
    for fname in fnames:
        field = self._fields[fname]
        if getattr(field, 'store') and getattr(field, 'compute'):
            self._recompute_todo(field)
        else:
            raise UserError(_('%s is not a stored compute/function field') % fname)
    self.recompute()
    return True


def _create_unique_index(self, cr, column, where_clause=None):
    if type(column) == list:
        column = ','.join(column)
    column_name = column.replace(' ', '').replace(',', '_')
    table = self._table
    index_name = 'uniq_%(table)s_%(column_name)s' % locals()
    cr.execute("SELECT relname FROM pg_class WHERE relname=%s", (index_name,))
    if not cr.rowcount:
        _logger.debug('Creating unique index %s' % index_name)
        query = "CREATE UNIQUE INDEX %(index_name)s ON %(table)s (%(column)s)"
        query += " WHERE %s" % (where_clause or "%(column)s IS NOT NULL")
        query = query % locals()
        cr.execute(query)


@api.model
def _read_group_process_groupby(self, gb, query):
    split = gb.split(':')
    field_type = self._fields[split[0]].type
    if field_type == 'datetime':
        gb_function = split[1] if len(split) == 2 else None
        tz_convert = field_type == 'datetime' and self._context.get('tz') in pytz.all_timezones
        qualified_field = self._inherits_join_calc(self._table, split[0], query)
        # Cfr: http://babel.pocoo.org/docs/dates/#date-fields
        display_formats = {
            'minute': 'dd MMM yyyy HH:mm',
            'hour': 'dd MMM yyyy  HH:mm',
            'day': 'dd MMM yyyy',  # yyyy = normal year
            'week': "'W'w YYYY",  # w YYYY = ISO week-year
            'month': 'MMMM yyyy',
            'quarter': 'QQQ yyyy',
            'year': 'yyyy',
        }
        time_intervals = {
            'minute': relativedelta(minutes=1),
            'hour': relativedelta(hours=1),
            'day': relativedelta(days=1),
            'week': timedelta(days=7),
            'month': relativedelta(months=1),
            'quarter': relativedelta(months=3),
            'year': relativedelta(years=1)
        }
        if tz_convert:
            qualified_field = "timezone('%s', timezone('UTC',%s))" % (self._context.get('tz', 'UTC'), qualified_field)
        qualified_field = "date_trunc('%s', %s)" % (gb_function or 'month', qualified_field)
        return {
            'field': split[0],
            'groupby': gb,
            'type': field_type,
            'display_format': display_formats[gb_function or 'month'],
            'interval': time_intervals[gb_function or 'month'],
            'tz_convert': tz_convert,
            'qualified_field': qualified_field,
        }
    return native_read_group_process_groupby(self, gb, query)


BaseModel.bulk_create = bulk_create
BaseModel.filtered_from_domain = filtered_from_domain
BaseModel.load = load
BaseModel.modified = modified
BaseModel.open_wizard = open_wizard
BaseModel.recompute_fields = recompute_fields
BaseModel.unlink = unlink
BaseModel._compare = _compare
BaseModel._create_unique_index = _create_unique_index
BaseModel._get_comparison_fields = _get_comparison_fields
BaseModel._get_comparison_logs = _get_comparison_logs
BaseModel._read_group_process_groupby = _read_group_process_groupby
BaseModel._try_lock = _try_lock
BaseModel._validate_fields = _validate_fields
