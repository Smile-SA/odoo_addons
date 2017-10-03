# -*- coding: utf-8 -*-

from odoo import fields
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


def format_date(date, date_format=DEFAULT_SERVER_DATE_FORMAT):
    if isinstance(date, basestring):
        date = fields.Date.from_string(date)
    return date.strftime(date_format)


def format_amount(amount, decimal_separator='.'):
    return truncate(amount, 2).replace('.', decimal_separator)


def truncate(f, n):
    """Truncates/pads a float f to n decimal places without rounding"""
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return '.'.join([i, (d + '0' * n)[:n]])
