# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
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

import csv
import inspect
import os

try:
    from openerp import tools  # From Odoo v6.1
except ImportError:
    import tools

from tools.func import wraps

CSV_SEPARATOR = ','
KEYS = ['name', 'module', 'result', 'code', 'file', 'line']


def logger(mapping):
    def decorator(method):
        @wraps(method)
        def wrapper(*args):
            vals = _get_vals(method, args, mapping)
            ignored_tests = []
            if tools.config.get('ignored_tests', ''):
                ignored_tests = tools.config.get('ignored_tests', '').replace(' ', '').split(',')
            if vals.get('file') in ignored_tests:
                vals['result'] = 'ignored'
                _write_log(vals)
                return
            try:
                res = method(*args)
            except Exception, e:
                vals['result'] = 'error'
                vals['name'] = repr(e)
                _write_log(vals)
                raise
            else:
                vals['result'] = 'success'
                _write_log(vals)
            return res
        return wrapper
    return decorator


def _get_args(method, arg_values):
    arg_names = inspect.getargspec(method).args
    args = {}.fromkeys(arg_names, False)
    for index, arg in enumerate(arg_names):
        if index < len(arg_values):
            args[arg] = arg_values[index]
    return args


def _get_vals(method, arg_values, mapping):
    args = _get_args(method, arg_values)
    vals = {}
    for k, v in mapping.iteritems():
        vals[k] = eval(v, args)
    return vals


def _write_log(vals):
    filename = tools.config.get('test_logfile')
    if not filename:
        return
    if not os.path.exists(filename):
        with open(filename, 'wb') as f:
            writer = csv.writer(f)
            writer.writerow(KEYS)
    with open(filename, 'ab') as f:
        writer = csv.writer(f)
        writer.writerow([vals.get(key, '') for key in KEYS])
