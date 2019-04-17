# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta
from six import string_types

from odoo import fields


def get_date(date, default_value=None):
    if isinstance(date, string_types):
        return fields.Date.from_string(date)
    return date or default_value


def get_fiscalyear_start_date(date, fiscalyear_start_day):
    date = get_date(date)
    fiscalyear_start_date = get_date(
        '%s-%s' % (date.year, fiscalyear_start_day))
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
    period_start_dates = get_period_start_dates(
        date, fiscalyear_start_day, depreciation_period)
    return max([p for p in period_start_dates if p <= date])


def get_period_stop_date(date, fiscalyear_start_day, depreciation_period):
    period_start_date = get_period_start_date(
        date, fiscalyear_start_day, depreciation_period)
    return period_start_date + relativedelta(
        months=depreciation_period, days=-1)


def get_period_days(date, fiscalyear_start_day, depreciation_period,
                    exact=False):
    period_stop_date = get_period_stop_date(
        date, fiscalyear_start_day, depreciation_period)
    if exact:
        period_start_date = get_period_start_date(
            date, fiscalyear_start_day, depreciation_period)
        return float((period_stop_date - period_start_date).days + 1)
    return depreciation_period * 30.0


def get_remaining_days(date, fiscalyear_start_day, exact=False,
                       first_day_acquisition=False):
    "Compute the number of remaining days until the end of fiscal year"
    date = get_date(date)
    first_day_acquisition = int(first_day_acquisition)
    if exact:
        fiscalyear_stop_date = get_fiscalyear_stop_date(
            date, fiscalyear_start_day)
        return (fiscalyear_stop_date - date).days + first_day_acquisition
    day, month = date.day, date.month
    return 30 - day + first_day_acquisition + (
        12 - month + int(fiscalyear_start_day[:2]) - 1) * 30


def get_prorata_temporis(date, fiscalyear_start_day, depreciation_period,
                         opposite=False, exact=False,
                         first_day_acquisition=False):
    days = get_remaining_days(
        date, fiscalyear_start_day, exact, first_day_acquisition)
    period_days = get_period_days(
        date, fiscalyear_start_day, depreciation_period, exact)
    period_stop_date = get_period_stop_date(
        date, fiscalyear_start_day, depreciation_period)
    next_start_date = period_stop_date + relativedelta(days=1)
    if next_start_date.strftime('%m-%d') == fiscalyear_start_day:
        days_after_period = 0
    else:
        days_after_period = get_remaining_days(
            next_start_date, fiscalyear_start_day, exact,
            first_day_acquisition)
    prorata = (days - days_after_period) / period_days
    if opposite:
        return 1 - prorata
    return prorata


def get_depreciation_period_dates(stop_date, fiscalyear_start_day,
                                  depreciation_period, start_date=None):
    period_dates = []
    period_stop_date = get_date(stop_date)
    period_start_date = get_fiscalyear_start_date(
        stop_date, fiscalyear_start_day)
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


def get_prorata_temporis_by_period(
        year_start_date, year_stop_date, fiscalyear_start_day,
        depreciation_period, exact=False, first_day_acquisition=False):
    prorata_temporis_by_period = {}
    year_start_date = get_date(year_start_date)
    year_stop_date = get_date(year_stop_date)
    for period_stop_date in get_depreciation_period_dates(
            year_stop_date, fiscalyear_start_day,
            depreciation_period, year_start_date):
        period_start_date = get_period_start_date(
            period_stop_date, fiscalyear_start_day, depreciation_period)
        date, opposite = period_start_date, False
        if period_start_date < year_start_date:
            date = year_start_date
        if period_stop_date >= year_stop_date:
            date, opposite = year_stop_date, True
        prorata_temporis_by_period[period_stop_date] = get_prorata_temporis(
            date, fiscalyear_start_day, depreciation_period, opposite, exact,
            first_day_acquisition)
    return prorata_temporis_by_period
