# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime
from dateutil.relativedelta import relativedelta
from six import string_types
import sys

from odoo.tools import float_round

from .date_utils import get_date, get_fiscalyear_start_date, \
    get_fiscalyear_stop_date, get_period_start_date, get_period_stop_date, \
    get_prorata_temporis, get_prorata_temporis_by_period, \
    get_depreciation_period_dates

if sys.version_info > (3,):
    long = int


class DepreciationBoard(object):

    def __init__(self, method_info, purchase_value, annuities, **kwargs):
        self.method_info = DepreciationBoard.check_and_format_method_info(
            method_info)
        self.purchase_value = purchase_value
        self.initial_annuities = annuities

        defaults = {
            'rate': 0.0,
            'salvage_value': 0.0,
            'depreciation_start_date': datetime.today(),
            'sale_date': None,
            'depreciation_period': 12,
            'fiscalyear_start_day': '01-01',
            'board_stop_date': None,
            'rounding': 2,
            'readonly_values': None,
            'exceptional_values': None,
            'prorata_temporis_exact': False,
            'first_day_acquisition': True,
        }
        for attr, default in defaults.items():
            value = kwargs.get(attr, default)
            if attr.endswith('_date'):
                value = get_date(value)
            elif attr.endswith('_values'):
                value = DepreciationBoard.check_and_format_vals(value, attr)
            elif attr == 'salvage_value' and \
                    not self.method_info['use_salvage_value']:
                value = default
            setattr(self, attr, value)

        assert self.depreciation_period in (1, 2, 3, 4, 6, 12), \
            'depreciation_period must be in (1, 2, 3, 4, 6, 12)'

        self.need_additional_annuity = \
            self.method_info['need_additional_annuity'] and \
            self.depreciation_start_date.strftime('%m-%d') != \
            self.fiscalyear_start_day
        self.first_yearly_depreciation_date = get_fiscalyear_stop_date(
            self.depreciation_start_date, self.fiscalyear_start_day)
        if self.sale_date and self.sale_date < \
                self.first_yearly_depreciation_date:
            self.first_yearly_depreciation_date = self.sale_date

    def reset(self):
        self.lines = []
        self.yearly_lines = []
        self.annuities = self.initial_annuities
        self.total_annuities = self.initial_annuities + \
            self.need_additional_annuity
        if self.board_stop_date:
            total_annuities = self.board_stop_date.year - \
                self.depreciation_start_date.year + 1
            if total_annuities < self.total_annuities:
                self.total_annuities = total_annuities
                self.need_additional_annuity = False
        self.annuity_number = 1
        fiscalyear_start_date = get_fiscalyear_start_date(
            self.depreciation_start_date, self.fiscalyear_start_day)
        exceptional_value_before_depreciation_start_date = sum(
            [self.exceptional_values[month]
             for month in self.exceptional_values
             if month < fiscalyear_start_date.strftime('%Y-%m')], 0)
        self.book_value = self.purchase_value - \
            exceptional_value_before_depreciation_start_date
        self.book_value_wo_exceptional = self.purchase_value - \
            exceptional_value_before_depreciation_start_date
        self.base_value = self.purchase_value - self.salvage_value - \
            exceptional_value_before_depreciation_start_date
        self.accumulated_value = 0.0
        self.accumulated_exceptional_value = \
            exceptional_value_before_depreciation_start_date
        self.next_depreciation_date = self.first_yearly_depreciation_date
        self.reset_partially = False

    @staticmethod
    def check_and_format_method_info(method_info):
        if not isinstance(method_info, dict):
            raise TypeError("method_info must be a dictionnary")
        all_keys = ('base_value', 'use_salvage_value', 'use_manual_rate',
                    'rate_formula', 'prorata', 'need_additional_annuity')
        missing_keys = []
        for key in all_keys:
            if key not in method_info:
                missing_keys.append(key)
        if missing_keys:
            raise KeyError("The following keys are missing in "
                           "method_info dict: %s" % missing_keys)
        return method_info

    @staticmethod
    def check_and_format_vals(vals, dict_name):
        error_msg = '%s keys must be strings at format YYYY-MM' % dict_name
        vals = vals or {}
        for k in vals:
            if not isinstance(k, string_types):
                raise ValueError(error_msg)
            else:
                try:
                    datetime.strptime(k, '%Y-%m')
                except ValueError:
                    raise ValueError(error_msg)
            if dict_name == 'exceptional_values':
                if isinstance(vals[k], (int, long)):
                    vals[k] = float(vals[k])
                if not isinstance(vals[k], float):
                    raise ValueError('%s values must be floats' % dict_name)
            if dict_name == 'readonly_values':
                error_msg2 = "%s values must be dictionaries " \
                             "{'depreciation_value': float, 'base_value': " \
                             "float}" % dict_name
                if not isinstance(vals[k], dict):
                    raise ValueError(error_msg2)
                else:
                    for k2 in ('depreciation_value', 'base_value'):
                        if k2 not in vals[k] or \
                                not isinstance(vals[k][k2], float):
                            raise ValueError(error_msg2)
        return vals

    def compute(self):
        self.reset()
        break_loop = False
        while not break_loop and \
                self.annuity_number <= self.total_annuities and \
                (not self.sale_date or
                 self.next_depreciation_date <= self.sale_date):
            if self.next_depreciation_date == self.sale_date:
                break_loop = True
            self.yearly_lines.append(self._get_next_yearly_line())
            self.annuity_number += 1
        for yearly_line in self.yearly_lines:
            self.lines.extend(yearly_line.get_periodical_lines(self))
        return self.get_lines()

    def _compute_depreciation_rate(self):
        localdict = {
            'length': float(self.annuities),
            'annuity_number': float(self.annuity_number),
        }
        if self.method_info['use_manual_rate']:
            localdict['rate'] = self.rate
        return eval(self.method_info['rate_formula'], localdict)

    def _get_prorata_temporis(self):
        if self.method_info['prorata']:
            if self.annuity_number == 1 and self.next_depreciation_date == \
                    self.first_yearly_depreciation_date:
                prorata = get_prorata_temporis(
                    self.depreciation_start_date, self.fiscalyear_start_day,
                    12, exact=self.prorata_temporis_exact,
                    first_day_acquisition=self.first_day_acquisition)
                if self.sale_date == self.next_depreciation_date:
                    prorata += get_prorata_temporis(
                        self.sale_date, self.fiscalyear_start_day, 12,
                        opposite=True, exact=self.prorata_temporis_exact,
                        first_day_acquisition=self.first_day_acquisition) - \
                        1.0
                return prorata
            if self.annuity_number > \
                    self.annuities + self.need_additional_annuity:
                return 0.0
            if self.sale_date and \
                    self.next_depreciation_date == self.sale_date:
                prorata = get_prorata_temporis(
                    self.sale_date, self.fiscalyear_start_day, 12,
                    opposite=True, exact=self.prorata_temporis_exact,
                    first_day_acquisition=self.first_day_acquisition)
                sale_fy_stop_date = get_fiscalyear_stop_date(
                    self.sale_date, self.fiscalyear_start_day)
                if self.board_stop_date:
                    board_fy_stop_date = get_fiscalyear_stop_date(
                        self.board_stop_date, self.fiscalyear_start_day)
                    if sale_fy_stop_date == board_fy_stop_date:
                        board_prorata = get_prorata_temporis(
                            self.depreciation_start_date,
                            self.fiscalyear_start_day, 12,
                            opposite=True, exact=self.prorata_temporis_exact,
                            first_day_acquisition=self.first_day_acquisition)
                        if board_prorata:
                            prorata /= board_prorata
                return prorata
            if self.sale_date and \
                    self.next_depreciation_date > self.sale_date:
                return 0.0
        return 1.0

    def _compute_depreciation_value(self):
        if self.annuity_number >= \
                self.annuities + self.need_additional_annuity:
            depr_value = self.book_value - self.salvage_value \
                if self.book_value else 0.0
        else:
            depr_value = self.base_value * \
                self._compute_depreciation_rate() / 100.0
        return float_round(depr_value * self._get_prorata_temporis(),
                           precision_digits=self.rounding)

    def _get_readonly_value(self):
        depreciation_value, readonly = 0.0, False
        last_year_month = self.next_depreciation_date.strftime('%Y-%m')
        if last_year_month in self.readonly_values:
            readonly = True
            depreciation_value = 0.0
            fiscalyear_start_date = get_fiscalyear_start_date(
                self.next_depreciation_date, self.fiscalyear_start_day)
            for month in self.readonly_values:
                if fiscalyear_start_date.strftime('%Y-%m') <= month <= \
                        self.next_depreciation_date.strftime('%Y-%m'):
                    depreciation_value += \
                        self.readonly_values[month]['depreciation_value']
            if round(self.readonly_values[last_year_month]['base_value'],
                     self.rounding) != round(self.base_value, self.rounding):
                # INFO: means that method changes occured
                self.base_value = \
                    self.readonly_values[last_year_month]['base_value']
                self.reset_partially = True
        return depreciation_value, readonly

    def _get_exceptional_value(self):
        exceptional_value = 0.0
        fiscalyear_start_date = self.next_depreciation_date + \
            relativedelta(years=-1, days=1)
        for month in self.exceptional_values:
            if fiscalyear_start_date.strftime('%Y-%m') <= month <= \
                    self.next_depreciation_date.strftime('%Y-%m'):
                exceptional_value += self.exceptional_values[month]
                self.reset_partially = True
        return exceptional_value

    def _get_next_yearly_line(self):
        depreciation_value, readonly = self._get_readonly_value()
        if not readonly:
            depreciation_value = self._compute_depreciation_value()
        self.accumulated_value += depreciation_value
        exceptional_value = self._get_exceptional_value()
        self.accumulated_exceptional_value += exceptional_value
        self.book_value_wo_exceptional = self.purchase_value - \
            self.accumulated_value
        self.book_value = self.book_value_wo_exceptional - \
            self.accumulated_exceptional_value
        vals = {
            'depreciation_date': self.next_depreciation_date,
            'base_value': self.base_value,
            'depreciation_value': depreciation_value,
            'accumulated_value': self.accumulated_value,
            'exceptional_value': exceptional_value,
            'book_value': self.book_value,
            'book_value_wo_exceptional': self.book_value_wo_exceptional,
            'rounding': self.rounding,
            'readonly': readonly,
        }
        self._compute_next_values()
        return DepreciationBoardLine(**vals)

    def _compute_next_values(self):
        self.next_depreciation_date += relativedelta(years=1)
        if self.sale_date and self.next_depreciation_date > self.sale_date:
            self.next_depreciation_date = self.sale_date
        if self.method_info['base_value'] == 'book_value' or \
                self.reset_partially:
            self.base_value = self.book_value - self.salvage_value
        if self.reset_partially:
            self.annuities -= self.annuity_number
            self.total_annuities -= self.annuity_number + \
                self.need_additional_annuity
            self.annuity_number = 0
            self.need_additional_annuity = False
            self.reset_partially = False

    def get_lines(self):
        return self.lines

    def pprint(self):
        from pprint import pprint
        return pprint(self.get_lines())


class DepreciationBoardLine(object):

    def __init__(self, depreciation_date, base_value, depreciation_value,
                 accumulated_value, book_value, exceptional_value=0.0,
                 book_value_wo_exceptional=0.0, readonly=False, rounding=2,
                 **kwargs):
        self.depreciation_date = depreciation_date
        self.base_value = float_round(
            base_value, precision_digits=rounding)
        self.depreciation_value = float_round(
            depreciation_value, precision_digits=rounding)
        self.accumulated_value = float_round(
            accumulated_value, precision_digits=rounding)
        self.book_value = float_round(
            book_value, precision_digits=rounding)
        self.exceptional_value = float_round(
            exceptional_value, precision_digits=rounding)
        self.book_value_wo_exceptional = float_round(
            book_value_wo_exceptional or book_value,
            precision_digits=rounding)
        self.readonly = readonly
        self.current_year_accumulated_value = float_round(
            kwargs.get(
                'current_year_accumulated_value',
                self.depreciation_value + self.exceptional_value),
            precision_digits=rounding)
        self.previous_years_accumulated_value = float_round(
            kwargs.get(
                'previous_years_accumulated_value',
                self.accumulated_value - self.depreciation_value +
                self.book_value_wo_exceptional - self.book_value -
                self.exceptional_value),
            precision_digits=rounding)

    def __repr__(self):
        return repr(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def _get_period_value(self, board, values, depreciation_date):
        period_value, exists = 0.0, False
        period_start_date = get_period_start_date(
            depreciation_date, board.fiscalyear_start_day,
            board.depreciation_period)
        if period_start_date < board.depreciation_start_date:
            period_start_date = board.depreciation_start_date
        for month in values:
            if period_start_date.strftime('%Y-%m') <= month <= \
                    depreciation_date.strftime('%Y-%m'):
                period_value += values[month]['depreciation_value'] \
                    if isinstance(values[month], dict) else values[month]
                exists = True
        return period_value, exists

    def _get_readonly_value(self, board, depreciation_date):
        return self._get_period_value(
            board, board.readonly_values, depreciation_date)

    def _get_exceptional_value(self, board, depreciation_date):
        return self._get_period_value(
            board, board.exceptional_values, depreciation_date)[0]

    def get_periodical_lines(self, board):
        # TODO: improve me
        if board.depreciation_period == 12:
            return [self]
        period_depreciation_start_date = get_period_start_date(
            self.depreciation_date, board.fiscalyear_start_day, 12)
        if period_depreciation_start_date < board.depreciation_start_date:
            period_depreciation_start_date = board.depreciation_start_date
        period_depreciation_stop_date = self.depreciation_date
        if board.board_stop_date and board.board_stop_date and \
                period_depreciation_stop_date > board.board_stop_date:
            period_depreciation_stop_date = get_period_stop_date(
                board.board_stop_date, board.fiscalyear_start_day,
                board.depreciation_period)
        prorata_temporis_by_period = get_prorata_temporis_by_period(
            period_depreciation_start_date, period_depreciation_stop_date,
            board.fiscalyear_start_day, board.depreciation_period,
            exact=board.prorata_temporis_exact,
            first_day_acquisition=board.first_day_acquisition)
        if not prorata_temporis_by_period:
            return []
        if board.method_info['need_additional_annuity'] and \
                board.board_stop_date and \
                period_depreciation_stop_date >= board.board_stop_date:
            real_end_date = period_depreciation_stop_date + \
                relativedelta(days=1) + \
                relativedelta(
                    month=board.depreciation_start_date.month,
                    day=board.depreciation_start_date.day) - \
                relativedelta(days=1)
            period_end_date = get_period_stop_date(
                real_end_date, board.fiscalyear_start_day,
                board.depreciation_period)
            period_dates = get_depreciation_period_dates(
                period_end_date, board.fiscalyear_start_day,
                board.depreciation_period)
            if real_end_date in period_dates:
                prorata_temporis_by_period[period_depreciation_stop_date] = 1.0
            else:
                prorata_temporis_by_period[period_depreciation_stop_date] = \
                    get_prorata_temporis(
                        real_end_date + relativedelta(days=1),
                        board.fiscalyear_start_day,
                        board.depreciation_period, opposite=True,
                        exact=board.prorata_temporis_exact,
                        first_day_acquisition=board.first_day_acquisition)
        lines = []
        total = sum(prorata_temporis_by_period.values())
        previous_accumulated_value = accumulated_value = \
            self.accumulated_value - self.depreciation_value
        book_value_wo_exceptional = \
            self.book_value_wo_exceptional + self.depreciation_value
        book_value = self.book_value + self.depreciation_value + \
            self.exceptional_value
        exceptional_value = gap = accumulated_value_in_period = 0.0
        depreciation_number = len(prorata_temporis_by_period)
        for depreciation_index, depreciation_date in enumerate(sorted(
                prorata_temporis_by_period)):
            readonly_depreciation_value, readonly = self._get_readonly_value(
                board, depreciation_date)
            exceptional_value = self._get_exceptional_value(
                board, depreciation_date)
            depreciation_value = float_round(
                self.depreciation_value *
                prorata_temporis_by_period[depreciation_date] / total,
                precision_digits=board.rounding)
            if readonly:
                gap += depreciation_value - readonly_depreciation_value
                depreciation_value = readonly_depreciation_value
            elif gap:
                depreciation_value += gap
                gap = 0.0
            if depreciation_index + 1 == depreciation_number:
                depreciation_value = self.depreciation_value - \
                    accumulated_value_in_period
                if depreciation_value + exceptional_value > book_value:
                    depreciation_value = book_value - exceptional_value
            else:
                accumulated_value_in_period += depreciation_value
            accumulated_value += depreciation_value
            book_value_wo_exceptional -= depreciation_value
            book_value -= depreciation_value + exceptional_value
            vals = {
                'depreciation_date': depreciation_date,
                'base_value': self.base_value,
                'depreciation_value': depreciation_value,
                'previous_years_accumulated_value':
                    previous_accumulated_value,
                'current_year_accumulated_value':
                    accumulated_value - previous_accumulated_value,
                'accumulated_value': accumulated_value,
                'exceptional_value': exceptional_value,
                'book_value': book_value,
                'book_value_wo_exceptional': book_value_wo_exceptional,
                'rounding': board.rounding,
                'readonly': readonly,
            }
            lines.append(DepreciationBoardLine(**vals))
        return lines
