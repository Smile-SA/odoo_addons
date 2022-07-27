# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import math
from six import string_types


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
        def format_args(k):
            return isinstance(k, string_types) and '"%s"' % k or k

        def format_kwargs(t):
            return '%s=%s' % (
                t[0], isinstance(t[1], string_types) and '"%s"' % t[1] or t[1])

        params = [', '.join(map(format_args, args)),
                  ', '.join(map(format_kwargs, kwargs.items()))]
        return unquote('%s(%s)' % (self, ', '.join(params)))

    def __repr__(self):
        return self
