# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta
from dateutil.relativedelta import relativedelta
import logging
from operator import and_, or_, sub
import psycopg2
import pytz

from odoo import api, tools, models, _
from odoo.exceptions import UserError, ValidationError

from ..tools import create_unique_index

_logger = logging.getLogger(__name__)

SET_OPERATORS = {"&": and_, "|": or_, "!": sub}
SQL2PYTHON_OPERATORS = {
    "=": "==",
    "<>": "!=",
    "like": "in",
    "ilike": "in",
    "not like": "not in",
    "not ilike": "not in",
}


class Base(models.AbstractModel):
    _inherit = 'base'

    def _validate_fields(self, fields_to_validate, excluded_names=()):
        if not self._context.get('no_validate'):
            try:
                super()._validate_fields(fields_to_validate, excluded_names)
            except ValidationError as e:
                name = e.args[0].replace(
                    "%s\n\n" % _("Error while validating constraint"), ""). \
                    replace("\nNone", "")
                raise ValidationError(name)

    @api.model
    def load(self, fields, data):
        res = super(Base, self.with_context(
            no_validate=True, defer_parent_store_computation=True)
        ).load(fields, data)
        ids = res['ids']
        if ids:
            recs = self.browse(ids)
            recs._validate_fields(fields)
            self._parent_store_compute()
        return res

    def unlink(self):
        # Force to call unlink method at removal of remote object linked
        # by a fields.many2one with ondelete='cascade'
        if hasattr(self.pool[self._name], '_cascade_relations'):
            self = self.with_context(active_test=False)
            if 'unlink_in_cascade' not in self._context:
                self = self.with_context(
                    unlink_in_cascade={self._name: list(self._ids)})
            for model, fnames in self.pool[self._name]. \
                    _cascade_relations.items():
                domain = ['|'] * (len(fnames) - 1) + \
                    [(fname, 'in', self._ids) for fname in fnames]
                SubModel = self.env[model]
                sub_models = SubModel.search(domain)
                sub_model_ids = list(set(sub_models._ids) - set(
                    self._context['unlink_in_cascade'].get(model, [])))
                if sub_model_ids:
                    self._context['unlink_in_cascade'].setdefault(model, []). \
                        extend(sub_model_ids)
                    SubModel.browse(sub_model_ids).unlink()
        if not self.exists():
            return True
        return super(Base, self).unlink()

    def modified(self, fnames, create=False, before=False):
        if self._context.get('recompute', True):
            super(Base, self).modified(fnames, create, before)

    def _try_lock(self, warning=None):
        try:
            self._cr.execute("""SELECT id FROM "%s" WHERE id IN %%s
                                FOR UPDATE NOWAIT""" % self._table,
                             (tuple(self.ids),), log_exceptions=False)
        except psycopg2.OperationalError:
            # INFO: Early rollback to allow translations
            # to work for the user feedback
            self._cr.rollback()
            if warning:
                raise UserError(warning)
            raise

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
                diff[field_name] = get_values(
                    self.env[field.comodel_name].
                    browse(diff[field_name]).name_get())
                label = _('New %s') % label
                separator = ', '
            if field.type == 'selection':
                selection = dict(field.selection)
                diff[field_name] = [selection[key] for key in diff[field_name]]
            log = separator.join(map(tools.ustr, diff[field_name]))
            logs.append('<b>%s</b>: %s' % (label, log))
        return logs

    def recompute_fields(self, fnames):
        for fname in fnames:
            field = self._fields[fname]
            if getattr(field, 'store') and getattr(field, 'compute'):
                self.env.add_to_compute(field, self)
            else:
                raise UserError(_('%s is not a stored compute/function field')
                                % fname)
        self.recompute(fnames, self)
        return True

    @api.model
    def _create_unique_index(self, column, where_clause=None):
        create_unique_index(self._cr, self._name, column, where_clause)

    @api.model
    def _read_group_process_groupby(self, gb, query):
        split = gb.split(':')
        field_type = self._fields[split[0]].type
        if field_type == 'datetime':
            gb_function = split[1] if len(split) == 2 else None
            tz_convert = field_type == 'datetime' and \
                self._context.get('tz') in pytz.all_timezones
            qualified_field = self._inherits_join_calc(
                self._table, split[0], query)
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
                qualified_field = "timezone('%s', timezone('UTC',%s))" % \
                    (self._context.get('tz', 'UTC'), qualified_field)
            qualified_field = "date_trunc('%s', %s)" % \
                (gb_function or 'month', qualified_field)
            return {
                'field': split[0],
                'groupby': gb,
                'type': field_type,
                'display_format': display_formats[gb_function or 'month'],
                'interval': time_intervals[gb_function or 'month'],
                'tz_convert': tz_convert,
                'qualified_field': qualified_field,
            }
        return super(Base, self)._read_group_process_groupby(gb, query)
