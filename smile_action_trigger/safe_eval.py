# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
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

"""
Overriding eval function defined in the base module
in order to complete globals_dict with missing Python __builtins__
"""

from base.ir import ir_actions

native_safe_eval = ir_actions.eval


def new_safe_eval(expr, globals_dict=None, locals_dict=None, mode="eval", nocopy=False):
    globals_dict = globals_dict or {}
    globals_dict.update({
        'divmod': divmod,
        'enumerate': enumerate,
        'float': float,
        'int': int,
        'isinstance': isinstance,
        'max': max,
        'min': min,
        'pow': pow,
        'range': range,
        'reversed': reversed,
        'sorted': sorted,
        'sum': sum,
        'type': type,
        'xrange': xrange,
        'zip': zip,
    })
    return native_safe_eval(expr, globals_dict, locals_dict, mode, nocopy)

ir_actions.eval = new_safe_eval
