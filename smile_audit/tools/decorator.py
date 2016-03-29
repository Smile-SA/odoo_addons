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


def _get_args(self, method, args, kwargs):
    # avoid hasattr(self, '_ids') because __getattr__() is overridden
    if '_ids' in self.__dict__:
        vals = method in ('create', 'write', '_create', '_write') and args[0] or {}
    else:
        cr, uid = args[:2]
        ids = method in ('write', 'unlink') and args[2] or []
        context = kwargs.get('context')
        self = self.browse(cr, uid, ids, context)
        vals = ('create' in method and args[2]) or ('write' in method and args[3]) or {}
    if self._name == 'res.users':
        vals = self._remove_reified_groups(vals)
    fields_to_read = vals.keys()
    if method in ('_create', '_write'):
        for index, fname in enumerate(fields_to_read):
            field = self._fields[fname]
            if not field.compute:
                del fields_to_read[index]
    return self, fields_to_read


def audit_decorator():
    def audit_wrapper(self, *args, **kwargs):
        origin = audit_wrapper.origin
        while hasattr(origin, 'origin'):
            origin = origin.origin
        method = origin.__name__
        records, fields_to_read = _get_args(self, method, args, kwargs)
        rule_obj = records.env['audit.rule']
        rule_id = rule_obj._model._check_audit_rule(records._cr).get(records._name, {}).get(method)
        if rule_id:
            rule = rule_obj.browse(rule_id)
            old_values = None
            if method != 'create':
                if fields_to_read or method == 'unlink':
                    old_values = records.read(fields_to_read, load='_classic_write')
                if method == 'unlink':
                    rule.log(method, old_values)
        result = audit_wrapper.origin(self, *args, **kwargs)
        if rule_id and method != 'unlink' and fields_to_read:
            if method == 'create':
                records = records.browse(result) if isinstance(result, (int, long)) else result
            new_values = records.read(fields_to_read, load='_classic_write')
            rule.log(method, old_values, new_values)
        return result
    return audit_wrapper
