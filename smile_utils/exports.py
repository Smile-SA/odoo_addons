# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
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

from decimal import Decimal
import logging
import unicodedata

_logger = logging.getLogger(__package__)


def strip_accents(string):
    return ''.join((c for c in unicodedata.normalize('NFD', string) if unicodedata.category(c) != 'Mn'))


def replace_non_ascii_by_space(string):
    return "".join([ord(i) < 128 and i or ' ' for i in string]).encode('ascii')


def clean_string(string):
    return replace_non_ascii_by_space(strip_accents(unicode(string)).upper())


class FixedLengthExport(object):

    def __init__(self, export_format, delimiter=''):
        assert isinstance(export_format, dict), 'export_format must be a dictionary with values of type tuple (position, type, length)'
        self._format = export_format
        self._columns = sorted(export_format, key=lambda x: export_format[x][0])
        self._delimiter = delimiter

    def _truncate(self, value, length):
        if len(value) > length:
            _logger.warning("FixedLengthExport: %s value is too long (max. length = %s)" % (value, length))
        return value[:length]

    def _format_string(self, value, length):
        value = clean_string(value or '').ljust(length)
        return self._truncate(value, length)

    def _format_integer(self, value, length):
        if isinstance(value, float):
            value = str(int(round(value)))
        value = str(value or 0).rjust(length, '0')[:length]
        return self._truncate(value, length)

    def _format_float(self, value, length):
        value = value or 0.0
        assert isinstance(value, (float, Decimal)), 'value must be a float: %s' % (value)
        format_string = '%%0%dd' % (length,)
        value = format_string % int(round((value or 0.0) * 100))
        return self._truncate(value, length)

    def format_row(self, data):
        res = []
        for column in self._columns:
            position, ttype, length = self._format[column]
            format_method_name = '_format_%s' % ttype
            if hasattr(self, format_method_name):
                format_method = getattr(self, format_method_name)
            else:
                format_method = self._truncate
            res.append(format_method(data.get(column), length))
        return self._delimiter.join(res)
