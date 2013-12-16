# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Casden (<http://www.casden.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import inspect


def get_original_method(method):
    while method.func_closure:
        method = method.func_closure[0].cell_contents
    return method


def check_if_not_decorated(method, decorator_method):
    if method.__name__ == decorator_method:
        return False
    while method.func_closure:
        if method.__name__ == decorator_method:
            return False
        method = method.func_closure[0].cell_contents
    return True


def _get_kwargs(method, args, kwargs):
    my_kwargs = kwargs and kwargs.copy() or {}
    argument_names = inspect.getargspec(method)[0]
    my_kwargs.update({}.fromkeys(argument_names, False))
    for index, arg in enumerate(argument_names):
        if index < len(args):
            my_kwargs[arg] = args[index]
    if 'context' not in my_kwargs or not isinstance(my_kwargs['context'], dict):
        my_kwargs['context'] = {}
    return my_kwargs


def get_method_args(method, args, kwargs):
    my_kwargs = _get_kwargs(method, args, kwargs)
    obj = my_kwargs['self']
    cr = my_kwargs.get('cr') or my_kwargs.get('cursor')
    uid = my_kwargs.get('uid') or my_kwargs.get('user')
    ids = my_kwargs.get('ids') or my_kwargs.get('id') or my_kwargs.get('id_') or []
    if isinstance(ids, (int, long)):
        ids = [ids]
    context = my_kwargs['context']
    return obj, cr, uid, ids, context
