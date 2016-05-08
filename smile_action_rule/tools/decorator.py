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

from openerp import _
from openerp.sql_db import Cursor
from openerp.exceptions import UserError


def _get_args(self, method, args, kwargs):
    # avoid hasattr(self, '_ids') because __getattr__() is overridden
    if '_ids' in self.__dict__:
        return self
    while True:
        if not hasattr(method, 'origin'):
            break
        method = method.origin
    method_arg_names = inspect.getargspec(method)[0][1:len(args) + 1]
    if not method_arg_names:
        decorator = method._api and method._api.__name__
        if decorator in ('multi', 'one'):
            method_arg_names = ['cr', 'uid', 'ids']
        elif decorator == 'model':
            method_arg_names = ['cr', 'uid']
        elif decorator.startswith('cr_'):
            method_arg_names = decorator.split('_')
        else:
            raise UserError(_('Method not adapted for action rules'))
        method_arg_names += [None] * (len(args) - len(method_arg_names))
    method_args = dict(zip(method_arg_names, args))
    cr = method_args.get('cr') or method_args.get('cursor')
    uid = method_args.get('uid') or method_args.get('user') or method_args.get('user_id')
    if not isinstance(cr, Cursor) or not isinstance(uid, (int, long)):
        raise UserError(_('Method not adapted for action rules'))
    ids = method_args.get('ids') or method_args.get('id')
    context = method_args.get('context') or {}
    if kwargs.get('context'):
        context.update(kwargs['context'])
    return self.browse(cr, uid, ids, context)


def _get_origin_method(method):
    if hasattr(method, '_orig'):
        return method._orig
    elif hasattr(method, 'origin'):
        return method.origin


def action_rule_decorator():
    def action_rule_wrapper(self, *args, **kwargs):

        method = action_rule_wrapper.origin
        records = _get_args(self, method, args, kwargs)

        # Avoid loops or cascading actions
        if '__action_done' not in records._context:
            records = records.with_context(__action_done={})

        # Retrieve the action rules to possibly execute
        rule_obj = records.env['base.action.rule']
        rule_ids = rule_obj._get_action_rules(self._name, method)
        rules = rule_obj.browse(rule_ids)

        # Check preconditions
        pre = {}
        for rule in rules:
            if rule.kind != 'on_create':
                pre[rule] = rule._filter_pre(records)
            if rule.kind == 'on_unlink':
                rule._process(rule._filter_post(records))

        # Read old values before the update
        old_values = {}
        if rules.filtered(lambda rule: '_write' in rule.kind):
            old_values = {old_vals.pop('id'): old_vals for old_vals in records.read()}

        # Call original method
        res = method(self, *args, **kwargs)

        # Manage create method
        origin = method
        while origin:
            if origin.__name__ == 'create':
                record = res
                if isinstance(res, (int, long)):
                    record = records.browse(res)
                pre = pre.fromkeys(rules, record)
                break
            origin = _get_origin_method(origin)

        # Check postconditions, and execute actions on the records that satisfy them
        for rule in rules.with_context(old_values=old_values):
            if rule.kind != 'on_unlink':
                rule._process(rule._filter_post(pre[rule]))

        return res
    return action_rule_wrapper
