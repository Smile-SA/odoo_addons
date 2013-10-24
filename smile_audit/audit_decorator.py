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

import inspect

from openerp import SUPERUSER_ID
from openerp.tools.func import wraps


def cache_restarter(original_method):
    @wraps(original_method)
    def wrapper(self, cr, module):
        res = original_method(self, cr, module)
        rule_obj = self.get('audit.rule')
        if rule_obj:
            rule_obj.clear_caches()
        return res
    return wrapper


def _get_args(method, args, kwargs):
    args_names = inspect.getargspec(method)[0]
    args_dict = {}.fromkeys(args_names, False)
    for index, arg in enumerate(args_names):
        if index < len(args):
            args_dict[arg] = args[index]
    obj = args_dict.get('obj') or args_dict.get('self', False)
    cr = args_dict.get('cursor') or args_dict.get('cr', False)
    uid = args_dict.get('uid') or args_dict.get('user', False)
    ids = args_dict.get('ids') or args_dict.get('id', [])
    vals = args_dict.get('values') or args_dict.get('vals', {})
    if isinstance(ids, (int, long)):
        ids = [ids]
    field_name = args_dict.get('name', '')
    context = isinstance(args_dict.get('context'), dict) and dict(args_dict['context']) or {}
    return obj, cr, uid, ids, field_name, vals, context


def _get_old_values(obj, cr, uid, ids, fields_list=None, context=None):
    if isinstance(ids, (int, long)):
        ids = [ids]
    old_values = {}
    for res_info in obj.read(cr, SUPERUSER_ID, ids, fields_list, context):
        old_values[res_info['id']] = res_info
    return old_values


def _get_original_method_name(method):
    while method.func_closure:
        method = method.func_closure[0].cell_contents
    return method.__name__


def audit_decorator(original_method):
    def audit_method(*args, **kwargs):
        # Get arguments
        obj, cr, uid, ids, field_name, vals, context = _get_args(original_method, args, kwargs)
        method_name = _get_original_method_name(original_method)
        rule_obj = obj.pool.get('audit.rule')
        rule_id = False
        if rule_obj and (method_name != 'write' or vals):  # To avoid to execute action if write({})
            # Search audit rule
            rule_id = rule_obj.check_rules(cr, uid, obj._name, method_name, context)
            # Save old values if audit rule exists
            if rule_id:
                fields_list = vals and vals.keys() or obj._columns.keys()
                context.update({
                    'method': method_name,
                    'active_object_ids': ids,
                    'fields_list': fields_list,
                    'old_values': _get_old_values(obj, cr, uid, ids, fields_list, context),
                })
                # Case: log unlink
                if method_name == 'unlink':
                    rule_obj.log(cr, uid, rule_id, context)
        # Execute original method
        result = original_method(*args, **kwargs)
        # Run audit rule if exists
        if rule_obj and rule_id and method_name != 'unlink':
            # Case: log create
            if method_name == 'create':
                context['active_object_ids'] = [result]
            rule_obj.log(cr, uid, rule_id, context)
        return result
    return audit_method
