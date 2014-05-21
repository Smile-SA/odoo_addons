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


def get_date(date, default_value=None):
    return isinstance(date, basestring) and datetime.strptime(date, '%Y-%m-%d') or date or default_value


def get_fiscalyear_start_date(date, fiscalyear_start_day):
    date = get_date(date)
    fiscalyear_start_date = datetime.strptime('%s-%s' % (date.year, fiscalyear_start_day), '%Y-%m-%d')
    if date < fiscalyear_start_date:
        fiscalyear_start_date += relativedelta(years=-1)
    return fiscalyear_start_date


def get_fiscalyear_stop_date(date, fiscalyear_start_day):
    period_start_date = get_fiscalyear_start_date(date, fiscalyear_start_day)
    return period_start_date + relativedelta(years=1, days=-1)


def get_period_start_dates(date, fiscalyear_start_day, depreciation_period):
    period_dates = []
    period_date = get_fiscalyear_start_date(date, fiscalyear_start_day)
    fiscalyear_stop_date = get_fiscalyear_stop_date(date, fiscalyear_start_day)
    while period_date < fiscalyear_stop_date:
        period_dates.append(period_date)
        period_date += relativedelta(months=depreciation_period)
    return period_dates


def get_period_start_date(date, fiscalyear_start_day, depreciation_period):
    date = get_date(date)
    period_start_dates = get_period_start_dates(date, fiscalyear_start_day, depreciation_period)
    return max([p for p in period_start_dates if p <= date])


def get_period_stop_date(date, fiscalyear_start_day, depreciation_period):
    period_start_date = get_period_start_date(date, fiscalyear_start_day, depreciation_period)
    return period_start_date + relativedelta(months=depreciation_period, days=-1)


def get_remaining_days(day, month, fiscalyear_start_day):
    "Compute the number of remaining days until the end of fiscal year"
    return 30 - day + 1 + (12 - month + int(fiscalyear_start_day[:2]) - 1) * 30


def get_prorata_temporis(date, fiscalyear_start_day, depreciation_period, opposite=False):
    date = get_date(date)
    days = get_remaining_days(date.day, date.month, fiscalyear_start_day)
    next_start_date = get_period_stop_date(date, fiscalyear_start_day, depreciation_period) + relativedelta(days=1)
    if next_start_date.strftime('%m-%d') == fiscalyear_start_day:
        days_after_period = 0
    else:
        days_after_period = get_remaining_days(next_start_date.day, next_start_date.month, fiscalyear_start_day)
    period_days = depreciation_period * 30.0
    prorata = (days - days_after_period) / period_days
    if opposite:
        return 1 - prorata
    return prorata


def get_depreciation_period_dates(stop_date, fiscalyear_start_day, depreciation_period, start_date=None):
    period_dates = []
    period_stop_date = get_date(stop_date)
    period_start_date = get_fiscalyear_start_date(stop_date, fiscalyear_start_day)
    period_date = get_fiscalyear_stop_date(stop_date, fiscalyear_start_day)
    start_date = get_date(start_date)
    if start_date and start_date >= period_start_date:
        period_start_date = start_date
    while period_date >= period_start_date:
        if period_date <= period_stop_date:
            period_dates.append(period_date)
        period_date += relativedelta(days=1)
        period_date -= relativedelta(months=depreciation_period, days=1)
    period_dates = period_dates[::-1]
    if period_stop_date not in period_dates:
        period_dates.append(period_stop_date)
    return period_dates


def get_prorata_temporis_by_period(year_start_date, year_stop_date, fiscalyear_start_day, depreciation_period):
    prorata_temporis_by_period = {}
    year_start_date = get_date(year_start_date)
    year_stop_date = get_date(year_stop_date)
    for period_stop_date in get_depreciation_period_dates(year_stop_date, fiscalyear_start_day, depreciation_period, year_start_date):
        period_start_date = get_period_start_date(period_stop_date, fiscalyear_start_day, depreciation_period)
        date, opposite = period_start_date, False
        if period_start_date < year_start_date:
            date = year_start_date
        if period_stop_date >= year_stop_date:
            date, opposite = year_stop_date, True
        prorata_temporis_by_period[period_stop_date] = get_prorata_temporis(date, fiscalyear_start_day, depreciation_period, opposite)
    return prorata_temporis_by_period
