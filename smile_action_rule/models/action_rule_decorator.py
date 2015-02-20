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
from openerp.exceptions import Warning


def _get_args(self, method, args, kwargs):
    # avoid hasattr(self, '_ids') because __getattr__() is overridden
    if '_ids' in self.__dict__:
        cr, uid, context = self.env.args
        ids = self._ids
    else:
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
            else:
                raise Warning(_('Method not adapted for action rules'))
            method_arg_names += [None] * (len(args) - len(method_arg_names))
        method_args = dict(zip(method_arg_names, args))
        cr = method_args.get('cr') or method_args.get('cursor')
        uid = method_args.get('uid') or method_args.get('user') or method_args.get('user_id')
        if not isinstance(cr, Cursor) or not isinstance(uid, (int, long)):
            raise Warning(_('Method not adapted for action rules'))
        ids = method_args.get('ids') or method_args.get('id')
        context = method_args.get('context') or kwargs.get('context')
    if isinstance(ids, (int, long)):
        ids = [ids]
    return cr, uid, ids, context


def action_rule_decorator():
    def action_rule_wrapper(self, *args, **kwargs):

        method = action_rule_wrapper.origin
        cr, uid, ids, context = _get_args(self, method, args, kwargs)

        # Avoid loops or cascading actions
        if context and context.get('action'):
            return method(self, *args, **kwargs)
        context = dict(context or {}, action=True)

        # Retrieve the action rules to possibly execute
        rule_obj = self.pool.get('base.action.rule')
        rules = rule_obj._get_action_rules(cr, uid, method, context)

        # Check preconditions
        pre_ids = {}
        for rule in rules:
            if rule.kind not in ('on_create', 'on_create_or_write'):
                pre_ids[rule] = rule_obj._filter(cr, uid, rule, rule.filter_pre_id, ids, context=context)
                if rule.kind == 'on_unlink' and pre_ids[rule]:
                    rule_obj._process(cr, uid, rule, pre_ids[rule], context=context)

        # Call original method
        res = method(self, *args, **kwargs)

        # Check postconditions, and execute actions on the records that satisfy them
        for rule in rules:
            if rule.kind != 'on_unlink':
                post_ids = rule_obj._filter(cr, uid, rule, rule.filter_id, pre_ids.get(rule), context=context)
                if post_ids:
                    rule_obj._process(cr, uid, rule, post_ids, context=context)

        return res
    return action_rule_wrapper
