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

from openerp.osv import fields
from openerp.tools.func import wraps

from sartre_tools import _get_browse_record_dict


def cache_restarter(original_method):
    @wraps(original_method)
    def wrapper(self, cr, module):
        res = original_method(self, cr, module)
        trigger_obj = self.get('sartre.trigger')
        if trigger_obj and hasattr(trigger_obj, 'cache_restart'):
            cr.execute("SELECT relname FROM pg_class WHERE relname=%s", (trigger_obj._table,))
            if cr.fetchall():
                trigger_obj.cache_restart(cr)
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


def _get_original_method_name(method):
    while method.func_closure:
        method = method.func_closure[0].cell_contents
    return method.__name__


def sartre_decorator(original_method):
    def trigger_method(*args, **kwargs):
        # Get arguments
        obj, cr, uid, ids, field_name, vals, context = _get_args(original_method, args, kwargs)
        method_name = _get_original_method_name(original_method)
        context['trigger'] = method_name
        trigger_obj = obj.pool.get('sartre.trigger')
        trigger_ids = []
        if trigger_obj \
                and (method_name != 'write' or vals):  # To avoid to execute action if write({})
            # Case: trigger on function
            calculation_method = False
            if method_name in ('get', 'set') and original_method.im_class == fields.function:
                calculation_method = method_name
                method_name = 'function'
            # Search triggers
            trigger_ids = trigger_obj.check_method_based_triggers(obj, cr, uid, method_name, field_name, calculation_method)
            # Save old values if triggers exist
            if trigger_ids:
                fields_list = trigger_obj.get_fields_to_save_old_values(cr, 1, trigger_ids)
                context.update({
                    'active_object_ids': ids,
                    'old_values': _get_browse_record_dict(obj, cr, uid, ids, fields_list, context),
                    'arg_values': vals,
                })
                # Case: trigger on unlink
                if method_name == 'unlink':
                    trigger_obj.run_now(cr, uid, trigger_ids, context=context)
        # Execute original method
        result = original_method(*args, **kwargs)
        # Run triggers if exists
        if trigger_obj and trigger_ids and method_name != 'unlink':
            # Case: trigger on create
            if method_name == 'create':
                context['active_object_ids'] = [result]
            trigger_obj.run_now(cr, uid, trigger_ids, context=context)
        return result
    return trigger_method
