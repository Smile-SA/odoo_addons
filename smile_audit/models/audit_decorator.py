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

from openerp.tools.func import wraps


def _get_args(self, method, args, kwargs):
    # avoid hasattr(self, '_ids') because __getattr__() is overridden
    if '_ids' in self.__dict__:
        cr, uid, context = self.env.args
        ids = self._ids
        vals = method in ('create', 'write') and args[0] or {}
    else:
        cr, uid = args[:2]
        ids = method in ('write', 'unlink') and args[2] or []
        vals = (method == 'create' and args[2]) or (method == 'write' and args[3]) or {}
        context = kwargs.get('context')
    if isinstance(ids, (int, long)):
        ids = [ids]
    return cr, uid, ids, vals, context


def audit_decorator(origin):
    @wraps(origin)
    def audit_wrapper(self, *args, **kwargs):
        method = origin.__name__
        cr, uid, ids, vals, context = _get_args(self, method, args, kwargs)
        rule_id = None
        if getattr(self, 'audit_rule', None):
            rule_obj = self.pool['audit.rule']
            rule_id = rule_obj._check_audit_rule(cr).get(self._name, {}).get(method)
        if rule_id:
            old_values = None
            if method != 'create':
                old_values = self.read(cr, uid, ids, vals.keys(), context, load='_classic_write')
                if method == 'unlink':
                    rule_obj.log(cr, uid, rule_id, method, old_values)
        result = origin(*args, **kwargs)
        if rule_id:
            new_values = None
            if audit_wrapper.origin.__name__ != 'unlink':
                if method == 'create':
                    ids = [result]
                new_values = self.read(cr, uid, ids, vals.keys(), context, load='_classic_write')
                rule_obj.log(cr, uid, rule_id, method, old_values, new_values)
        return result
    return audit_wrapper
