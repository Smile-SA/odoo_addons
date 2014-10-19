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
import time

try:
    from openerp import tools  # From Odoo v6.1
except ImportError:
    import tools


CSV_SEPARATOR = ','
KEYS = ['module', 'result', 'code', 'file', 'line', 'exception', 'duration']


def _get_filename(filepath, module):
    dirname, basename = os.path.split(filepath)
    dirname = dirname.replace(os.path.join(dirname.split(module)[0], module), '')
    if dirname.startswith(os.path.sep):
        dirname = dirname[len(os.path.sep):]
    return os.path.join(dirname, basename)


def logger(mapping):
    def decorator(method):
        @tools.func.wraps(method)
        def wrapper(*args, **kwargs):
            vals = _get_vals(method, args, kwargs, mapping)
            if tools.config.get('ignored_tests') and vals.get('module'):
                try:
                    ignored_tests = eval(tools.config.get('ignored_tests')).get(vals['module']) or []
                except (NameError, SyntaxError):
                    ignored_tests = []
                if ignored_tests == 'all' or \
                        (vals.get('file') and _get_filename(vals['file'], vals['module']) in ignored_tests):
                    vals['result'] = 'ignored'
                    _write_log(vals)
                    return
            try:
                t0 = time.time()
                res = method(*args, **kwargs)
            except Exception, e:
                vals['duration'] = time.time() - t0
                vals['result'] = 'error'
                vals['exception'] = repr(e)
                _write_log(vals)
                raise
            else:
                vals['duration'] = time.time() - t0
                vals['result'] = 'success'
                _write_log(vals)
            return res
        return wrapper
    return decorator


def _get_args(method, arg_values, kwarg_values):
    arg_names = inspect.getargspec(method).args
    args = {}.fromkeys(arg_names, False)
    for index, arg in enumerate(arg_names):
        if index < len(arg_values):
            args[arg] = arg_values[index]
    args.update(kwarg_values)
    return args


def _get_vals(method, arg_values, kwarg_values, mapping):
    args = _get_args(method, arg_values, kwarg_values)
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
