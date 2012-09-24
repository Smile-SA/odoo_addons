# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Smile (<http://www.smile.fr>). All Rights Reserved
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

DEPRECIATION_METHODS = ['linear', 'degressive']


def get_period_start_days(fiscalyear_start_day, period_length):
    fiscalyear_start_date = datetime.strptime('2000-%s' % fiscalyear_start_day, '%Y-%m-%d')
    fiscalyear_stop_date = fiscalyear_start_date + relativedelta(years=1, days=-1)
    period_date = fiscalyear_start_date
    period_dates = []
    while period_date < fiscalyear_stop_date:
        period_dates.append(period_date)
        period_date += relativedelta(months=period_length)
    return map(lambda d: d.strftime('%m-%d'), period_dates)


def get_period_start_date(date, period_start_days):
    if isinstance(date, basestring):
        date = datetime.strptime(date, '%Y-%m-%d')
    day = date.strftime('%m-%d')
    period_start_day = max([p for p in period_start_days if p <= day])
    return datetime(date.year, int(period_start_day[:2]), int(period_start_day[-2:]))


def get_period_stop_date(date, period_start_days, period_length):
    period_start_date = get_period_start_date(date, period_start_days)
    return period_start_date + relativedelta(months=period_length, days=-1)


def get_prorata_rate(date, period_start_date, period_length):
    next_period_start_date = period_start_date + relativedelta(months=period_length)
    period_days = (next_period_start_date - period_start_date).days
    return float((next_period_start_date - date).days) / period_days


def _check_and_format_vals(vals, dict_name):
    error_msg = '%s keys must be strings at format YYYY-MM' % dict_name
    vals = vals or {}
    for k in vals:
        if not isinstance(k, basestring):
            raise ValueError(error_msg)
        else:
            try:
                datetime.strptime(k, '%Y-%m')
            except ValueError:
                raise ValueError(error_msg)
        if isinstance(vals[k], (int, long)):
            vals[k] = float(vals[k])
        if not isinstance(vals[k], float):
            raise ValueError('%s values must be floats' % dict_name)
    return vals


class DepreciationBoard(object):
    def __init__(self, gross_value, method, periods, degressive_rate=0.0, prorata=True, salvage_value=0.0, depreciation_start_date=None,
                 readonly_values=None, exceptional_values=None, fiscalyear_start_day='01-01', period_length=12, accounting_periods=0, rounding=2,
                 disposal_date=None):
        assert period_length in (1, 2, 3, 4, 6, 12), 'period_length must be in (1, 2, 3, 4, 6, 12)'
        assert method in DEPRECIATION_METHODS, 'method must be in %s' % DEPRECIATION_METHODS
        self.gross_value = gross_value
        self.method = method
        self.method_periods = periods
        self.period_length = period_length
        self.accounting_periods = accounting_periods or periods
        self.degressive_rate = degressive_rate
        self.prorata = prorata
        self.salvage_value = salvage_value
        self.depreciation_start_date = isinstance(depreciation_start_date, basestring) and datetime.strptime(depreciation_start_date, '%Y-%m-%d') \
            or depreciation_start_date or datetime.today()
        self.readonly_values = _check_and_format_vals(readonly_values, 'readonly_values')
        self.exceptional_values = _check_and_format_vals(exceptional_values, 'readonly_values')
        self.period_start_days = get_period_start_days(fiscalyear_start_day, period_length)
        self.rounding = rounding
        self.disposal_date = isinstance(disposal_date, basestring) and datetime.strptime(disposal_date, '%Y-%m-%d') or disposal_date or None
        self.disposal_period_start_day = self.disposal_period_stop_day = None
        if self.disposal_date:
            self.disposal_period_start_day = get_period_start_date(self.disposal_date, self.period_start_days)
            self.disposal_period_stop_day = self.disposal_period_start_day + relativedelta(months=self.period_length, days=-1)
        self.reset()

    def reset(self):
        self.lines = []
        self.depreciation_position = 0
        self.base_value = self.gross_value - self.salvage_value
        self.periods = self.method_periods
        self.total_periods = self.accounting_periods
        self.accumulated_value = 0.0
        self.accumulated_exceptional_value = 0.0
        self.book_value = self.gross_value
        self.book_value_wo_exceptional = self.gross_value
        self.next_depreciation_date = get_period_stop_date(self.depreciation_start_date, self.period_start_days, self.period_length)
        self.period_start_date = get_period_start_date(self.next_depreciation_date, self.period_start_days)
        self.prorata_rate = get_prorata_rate(self.depreciation_start_date, self.period_start_date, self.period_length)
        self.starts_on_period_start_day = self.depreciation_start_date.strftime('%m-%d') in self.period_start_days
        self.is_linear_and_doesnt_start_on_period_start_day = self.method == 'linear' and not self.starts_on_period_start_day

    def get_lines(self):
        return self.lines

    def compute(self):
        self.reset()
        while self.depreciation_position < self.total_periods + self.is_linear_and_doesnt_start_on_period_start_day \
                and (not self.disposal_period_stop_day or self.next_depreciation_date <= self.disposal_period_stop_day):
            self.depreciation_position += 1
            self._get_next_line()
        return self.get_lines()

    def _get_next_line(self):
        reset_partially = force_starts_on_period_start_day = readonly = False
        if self.period_start_date.strftime('%Y-%m') in self.readonly_values:
            depreciation_value = self.readonly_values[self.period_start_date.strftime('%Y-%m')]
            reset_partially = readonly = True
        else:
            depreciation_value = getattr(self, '_compute_%s_amortization' % self.method)()
        if self.period_start_date == self.disposal_period_start_day:
            depreciation_value *= (self.disposal_date - self.disposal_period_start_day).days
            depreciation_value /= (self.disposal_period_stop_day - self.disposal_period_start_day).days
        self.accumulated_value += depreciation_value
        exceptional_value = 0.0
        if self.method_periods == self.accounting_periods \
                or self.depreciation_position <= self.periods:
            exceptional_value = self.exceptional_values.get(self.period_start_date.strftime('%Y-%m'), 0.0)
            if exceptional_value:
                reset_partially = force_starts_on_period_start_day = True
        self.accumulated_exceptional_value += exceptional_value
        self.book_value_wo_exceptional = self.gross_value - self.accumulated_value
        self.book_value = self.book_value_wo_exceptional - self.accumulated_exceptional_value
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
        self.lines.append(DepreciationBoardLine(**vals))
        self.next_depreciation_date += relativedelta(day=1) + relativedelta(months=self.period_length + 1, days=-1)
        self.period_start_date += relativedelta(months=self.period_length)
        if self.method == 'degressive':
            self.base_value -= depreciation_value
        if reset_partially:
            self._reset_partially(force_starts_on_period_start_day)

    def _compute_linear_amortization(self):
        depreciation_value = self.base_value / self.periods
        if not self.starts_on_period_start_day and self.depreciation_position == 1:
            depreciation_value *= self.prorata_rate
        elif not self.starts_on_period_start_day and self.depreciation_position == self.periods + 1:
            depreciation_value *= 1 - self.prorata_rate
        elif self.depreciation_position > self.periods:
            depreciation_value = 0.0
        return depreciation_value

    def _compute_degressive_amortization(self):
        depreciation_value = self.base_value * self.degressive_rate / 100.0
        if self.depreciation_position == 1:
            depreciation_value *= self.prorata_rate
        remaining_periods = self.periods - self.depreciation_position + 1
        if remaining_periods <= 0:
            depreciation_value = 0.0
        elif self.degressive_rate <= 100 / remaining_periods:
            depreciation_value = self.base_value / remaining_periods
        return depreciation_value

    def _reset_partially(self, force_starts_on_period_start_day=False):
        self.periods -= self.depreciation_position
        self.total_periods -= self.depreciation_position
        self.depreciation_position = 0
        self.base_value = self.book_value - self.salvage_value
        if force_starts_on_period_start_day:
            self.starts_on_period_start_day = True
            self.is_linear_and_doesnt_start_on_period_start_day = False

    def pprint(self):
        from pprint import pprint
        return pprint(self.get_lines())


class DepreciationBoardLine(object):
    def __init__(self, depreciation_date, base_value, depreciation_value, accumulated_value, book_value,
                 exceptional_value=0.0, book_value_wo_exceptional=0.0, readonly=False, rounding=2):
        self.depreciation_date = depreciation_date
        self.base_value = round(base_value, rounding)
        self.depreciation_value = round(depreciation_value, rounding)
        self.accumulated_value = round(accumulated_value, rounding)
        self.book_value = round(book_value, rounding)
        self.exceptional_value = round(exceptional_value, rounding)
        self.book_value_wo_exceptional = round(book_value_wo_exceptional or book_value, rounding)
        self.readonly = readonly

    def __repr__(self):
        return repr(self.__dict__)

    def __str__(self):
        return str(self.__dict__)
