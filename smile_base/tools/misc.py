# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import math


def float_time_convert(float_val):
    """
    Converts a float in time (hour, minute).

    @param float_val: float, obtained via widget float_time in Odoo interface
    @return: (int, int), a tuple hours and minutes
    """
    factor = float_val < 0 and -1 or 1
    val = abs(float_val)
    return factor * int(math.floor(val)), int(round((val % 1) * 60))


def float_to_strtime(float_time):
    """
    :param hour: float
    :param minute: float
    :return: str
    """
    return '{:02d}:{:02d}'.format(*float_time_convert(float_time))


class unquote(str):

    def __getitem__(self, key):
        return unquote('%s[%s]' % (self, key))

    def __getattribute__(self, attr):
        return unquote('%s.%s' % (self, attr))

    def __call__(self, *args, **kwargs):
        format_args = lambda k: isinstance(k, basestring) and '"%s"' % k or k
        format_kwargs = lambda (k, v): '%s=%s' % (k, isinstance(v, basestring) and '"%s"' % v or v)
        params = [', '.join(map(format_args, args)),
                  ', '.join(map(format_kwargs, kwargs.iteritems()))]
        return unquote('%s(%s)' % (self, ', '.join(params)))

    def __repr__(self):
        return self
