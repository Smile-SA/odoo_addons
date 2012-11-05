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


def get_date(date, default_value=None):
    return isinstance(date, basestring) and datetime.strptime(date, '%Y-%m-%d') or date or default_value


def get_fiscalyear_start_date(date, fiscalyear_start_day):
    if isinstance(date, basestring):
        date = datetime.strptime(date, '%Y-%m-%d')
    return datetime.strptime('%s-%s' % (date.year, fiscalyear_start_day), '%Y-%m-%d')


def get_fiscalyear_stop_date(date, fiscalyear_start_day):
    period_start_date = get_fiscalyear_start_date(date, fiscalyear_start_day)
    return period_start_date + relativedelta(years=1, days=-1)


def check_and_format_vals(vals, dict_name):
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


def get_prorata_temporis(date, period_start_day, opposite=False, period_length=12):
    period_start_date = datetime.strptime('%s-%s' % (date.year, period_start_day), '%Y-%m-%d')
    if date < period_start_date:
        period_start_date += relativedelta(months=-period_length)
    next_period_start_date = period_start_date + relativedelta(months=period_length)
    period_days = (next_period_start_date - period_start_date).days
    days = (date - period_start_date).days + 1.0
    if opposite:
        return days / period_days
    return 1 - days / period_days


class DepreciationBoard(object):

    def __init__(self, gross_value, method, years, degressive_rate=0.0, salvage_value=0.0, depreciation_start_date=None,
                 starts_on_first_day_of_month=False, disposal_date=None, period_length=12,
                 readonly_values=None, exceptional_values=None, fiscalyear_start_day='01-01', accounting_years=0, rounding=2):

        assert period_length in (1, 2, 3, 4, 6, 12), 'period_length must be in (1, 2, 3, 4, 6, 12)'
        assert method in DEPRECIATION_METHODS, 'method must be in %s' % DEPRECIATION_METHODS

        self.gross_value = gross_value
        self.method = method
        self.method_years = years
        self.degressive_rate = degressive_rate
        self.salvage_value = salvage_value
        self.depreciation_start_date = get_date(depreciation_start_date, datetime.today())
        if starts_on_first_day_of_month:
            self.depreciation_start_date += relativedelta(day=1)
        self.readonly_values = check_and_format_vals(readonly_values, 'readonly_values')
        self.exceptional_values = check_and_format_vals(exceptional_values, 'readonly_values')
        self.fiscalyear_start_day = fiscalyear_start_day
        self.period_length = period_length
        self.accounting_years = accounting_years or years
        self.rounding = rounding
        self.disposal_date = get_date(disposal_date)

        self.prorata_temporis = get_prorata_temporis(self.depreciation_start_date, self.fiscalyear_start_day)
        if self.disposal_date:
            self.disposal_fiscalyear_stop_date = get_fiscalyear_stop_date(self.disposal_date, self.fiscalyear_start_day)
        self.reset()

    def reset(self):
        self.lines = []
        self.yearly_lines = []
        self.depreciation_position = 0
        self.base_value = self.gross_value - self.salvage_value
        self.years = self.method_years
        self.total_years = self.accounting_years
        self.accumulated_value = 0.0
        self.accumulated_exceptional_value = 0.0
        self.book_value = self.gross_value
        self.book_value_wo_exceptional = self.gross_value
        self.next_depreciation_date = get_fiscalyear_stop_date(self.depreciation_start_date, self.fiscalyear_start_day)
        self.starts_on_fiscalyear_start_day = self.depreciation_start_date.strftime('%m-%d') == self.fiscalyear_start_day
        self.is_linear_and_doesnt_start_on_fiscalyear_start_day = self.method == 'linear' and not self.starts_on_fiscalyear_start_day
        self.reset_partially = False

    def compute(self):
        self.reset()
        while self.depreciation_position < (self.total_years + self.is_linear_and_doesnt_start_on_fiscalyear_start_day) \
                and (not self.disposal_date or self.next_depreciation_date <= self.disposal_fiscalyear_stop_date):
            self.depreciation_position += 1
            self._get_next_yearly_line()
        for yearly_line in self.yearly_lines:
            self.lines.extend(yearly_line.get_periodical_lines(self))
        return self.get_lines()

    def _get_next_yearly_line(self):
        depreciation_date = self.next_depreciation_date
        depreciation_value, new_base_value, readonly = getattr(self, '_compute_%s_amortization' % self.method)()
        if self.disposal_date and self.next_depreciation_date == self.disposal_fiscalyear_stop_date:
            depreciation_date = self.disposal_date
            depreciation_value *= get_prorata_temporis(self.disposal_date, self.fiscalyear_start_day, opposite=True)
        exceptional_value = self._get_exceptional_value()
        self.accumulated_value += depreciation_value
        self.accumulated_exceptional_value += exceptional_value
        self.book_value_wo_exceptional = self.gross_value - self.accumulated_value
        self.book_value = self.book_value_wo_exceptional - self.accumulated_exceptional_value
        vals = {
            'depreciation_date': depreciation_date,
            'base_value': self.base_value,
            'depreciation_value': depreciation_value,
            'accumulated_value': self.accumulated_value,
            'exceptional_value': exceptional_value,
            'book_value': self.book_value,
            'book_value_wo_exceptional': self.book_value_wo_exceptional,
            'rounding': self.rounding,
            'readonly': readonly,
        }
        self.yearly_lines.append(DepreciationBoardLine(**vals))
        self.next_depreciation_date += relativedelta(years=1)
        self.base_value = new_base_value
        self._reset_partially()

    def _get_readonly_value(self):
        depreciation_value = 0.0
        readonly = False
        if self.next_depreciation_date.strftime('%Y-%m') in self.readonly_values:
            fiscalyear_start_date = self.next_depreciation_date + relativedelta(years=-1, days=1)
            for month in self.readonly_values:
                if fiscalyear_start_date.strftime('%Y-%m') <= month <= self.next_depreciation_date.strftime('%Y-%m'):
                    depreciation_value += self.readonly_values[month]
            readonly = True
            self.reset_partially = True
        return depreciation_value, readonly

    def _compute_linear_amortization(self):
        depreciation_value, readonly = self._get_readonly_value()
        if not depreciation_value:
            depreciation_value = self.base_value / self.years
            if not self.starts_on_fiscalyear_start_day and self.depreciation_position == 1:
                depreciation_value *= self.prorata_temporis
            elif not self.starts_on_fiscalyear_start_day and self.depreciation_position == self.years + 1:
                depreciation_value = self.book_value - self.salvage_value
            elif self.depreciation_position > self.years:
                depreciation_value = 0.0
        return depreciation_value, self.base_value, readonly

    def _compute_degressive_amortization(self):
        depreciation_value, readonly = self._get_readonly_value()
        if not depreciation_value:
            depreciation_value = self.base_value * self.degressive_rate / 100.0
            if self.depreciation_position == 1:
                depreciation_value *= self.prorata_temporis
            remaining_years = self.years - self.depreciation_position + 1
            if remaining_years <= 0:
                depreciation_value = 0.0
            elif self.degressive_rate <= 100 / remaining_years:
                depreciation_value = self.base_value / remaining_years
        new_base_value = self.base_value - depreciation_value
        return depreciation_value, new_base_value, readonly

    def _get_exceptional_value(self):
        exceptional_value = 0.0
        if self.depreciation_position <= (self.years + self.is_linear_and_doesnt_start_on_fiscalyear_start_day):
            fiscalyear_start_date = self.next_depreciation_date + relativedelta(years=-1, days=1)
            for month in self.exceptional_values:
                if fiscalyear_start_date.strftime('%Y-%m') <= month <= self.next_depreciation_date.strftime('%Y-%m'):
                    exceptional_value += self.exceptional_values[month]
            if exceptional_value:
                self.starts_on_fiscalyear_start_day = True
                self.is_linear_and_doesnt_start_on_fiscalyear_start_day = False
                self.reset_partially = True
        return exceptional_value

    def _reset_partially(self):
        if self.reset_partially:
            self.years -= self.depreciation_position
            self.total_years -= self.depreciation_position
            self.depreciation_position = 0
            self.base_value = self.book_value - self.salvage_value
            self.reset_partially = False

    def get_lines(self):
        return self.lines

    def pprint(self):
        from pprint import pprint
        return pprint(self.get_lines())


def _get_period_start_days(date, fiscalyear_start_day, period_length):
    year = date.year - (date.strftime('%m-%s') < fiscalyear_start_day)
    fiscalyear_start_date = datetime.strptime('%s-%s' % (year, fiscalyear_start_day), '%Y-%m-%d')
    fiscalyear_stop_date = fiscalyear_start_date + relativedelta(years=1, days=-1)
    period_date = fiscalyear_start_date
    period_dates = []
    while period_date < fiscalyear_stop_date:
        period_dates.append(period_date)
        period_date += relativedelta(months=period_length)
    return map(lambda d: d.strftime('%m-%d'), period_dates)


def get_period_start_date(date, fiscalyear_start_day, period_length):
    if isinstance(date, basestring):
        date = datetime.strptime(date, '%Y-%m-%d')
    day = date.strftime('%m-%d')
    period_start_days = _get_period_start_days(date, fiscalyear_start_day, period_length)
    period_start_day = max([p for p in period_start_days if p <= day])
    return datetime.strptime('%s-%s' % (date.year, period_start_day), '%Y-%m-%d')


def get_period_stop_date(date, fiscalyear_start_day, period_length):
    period_start_date = get_period_start_date(date, fiscalyear_start_day, period_length)
    return period_start_date + relativedelta(months=period_length, days=-1)


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

    def get_periodical_lines(self, board):
        lines = []
        period_dates = self._get_period_stop_dates(board)
        if not period_dates:
            return lines
        depreciation_start_period_date = period_dates[0] + relativedelta(day=1) + relativedelta(months=-board.period_length + 1)
        remaining_depreciation_number = self._get_remaining_depreciation_number(board, period_dates, depreciation_start_period_date)
        remaining_yearly_depreciation_value = self.depreciation_value
        accumulated_value = self.accumulated_value - self.depreciation_value
        book_value_wo_exceptional = self.book_value_wo_exceptional + self.depreciation_value
        book_value = self.book_value + self.depreciation_value + self.exceptional_value
        for depreciation_date in period_dates:
            depreciation_rate = 1
            period_stop_date = depreciation_date
            if board.disposal_date and depreciation_date == board.disposal_date:
                period_stop_date = get_period_stop_date(depreciation_date, board.fiscalyear_start_day, board.period_length)
            if period_stop_date.strftime('%Y-%m') in board.readonly_values:
                depreciation_value = board.readonly_values[period_stop_date.strftime('%Y-%m')]
                readonly = True
            else:
                if depreciation_date == period_dates[0] and board.depreciation_start_date >= depreciation_start_period_date:
                    depreciation_rate = remaining_depreciation_number - int(remaining_depreciation_number)
                    if not depreciation_rate:
                        depreciation_rate = 1
                depreciation_value = min(remaining_depreciation_number and remaining_yearly_depreciation_value /
                                         remaining_depreciation_number * depreciation_rate or 0.0,
                                         remaining_yearly_depreciation_value)
                readonly = False
            remaining_yearly_depreciation_value -= depreciation_value
            remaining_depreciation_number -= depreciation_rate
            accumulated_value += depreciation_value
            exceptional_value = depreciation_date == period_dates[-1] and self.exceptional_value or 0.0
            book_value -= depreciation_value + exceptional_value
            book_value_wo_exceptional -= depreciation_value
            vals = {
                'depreciation_date': depreciation_date,
                'base_value': self.base_value,
                'depreciation_value': depreciation_value,
                'accumulated_value': accumulated_value,
                'exceptional_value': exceptional_value,
                'book_value': book_value,
                'book_value_wo_exceptional': book_value_wo_exceptional,
                'rounding': board.rounding,
                'readonly': readonly,
            }
            lines.append(DepreciationBoardLine(**vals))
        return lines

    def _get_remaining_depreciation_number(self, board, period_dates, depreciation_start_period_date):
        remaining_depreciation_number = len(period_dates)
        if board.depreciation_start_date >= depreciation_start_period_date:
            remaining_depreciation_number -= get_prorata_temporis(board.depreciation_start_date, depreciation_start_period_date.strftime('%m-%d'),
                                                                  period_length=board.period_length, opposite=True)
        if (board.depreciation_start_date + relativedelta(years=board.method_years)) <= period_dates[-1]:
            period_start_date = period_dates[-1] + relativedelta(day=1) + relativedelta(months=-board.period_length + 1)
            remaining_depreciation_number -= get_prorata_temporis(board.depreciation_start_date, period_start_date.strftime('%m-%d'),
                                                                  period_length=board.period_length)
        return remaining_depreciation_number

    def _get_period_stop_dates(self, board):
        fiscalyear_start_date = get_fiscalyear_start_date(self.depreciation_date, board.fiscalyear_start_day)
        fiscalyear_stop_date = get_fiscalyear_stop_date(self.depreciation_date, board.fiscalyear_start_day)
        period_date = fiscalyear_start_date + relativedelta(months=board.period_length, days=-1)
        period_dates = []
        while period_date <= fiscalyear_stop_date:
            period_dates.append(period_date)
            period_date += relativedelta(day=1) + relativedelta(months=board.period_length + 1, days=-1)
        start_period_date = max(get_fiscalyear_start_date(self.depreciation_date, board.fiscalyear_start_day), board.depreciation_start_date)
        stop_period_date = self.depreciation_date
        if board.disposal_date:
            if board.disposal_date not in period_dates:
                period_dates.append(board.disposal_date)
            stop_period_date = min(stop_period_date, board.disposal_date)
        else:
            depreciation_stop_date = board.depreciation_start_date + relativedelta(years=board.method_years, days=-1)
            if depreciation_stop_date not in period_dates:
                depreciation_stop_date += relativedelta(months=board.period_length)
            stop_period_date = min(stop_period_date, depreciation_stop_date)
        return [period_date for period_date in period_dates if start_period_date <= period_date <= stop_period_date]
