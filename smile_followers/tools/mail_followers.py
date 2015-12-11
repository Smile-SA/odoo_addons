# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>).
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

from openerp import SUPERUSER_ID


def _get_args(self, args, kwargs):
    if hasattr(self, 'env'):
        cr, uid, context = self.env.args
        ids = self.ids
        vals = args[0]
    else:
        cr, uid = args[:2]
        if isinstance(args[2], dict):
            ids, vals = [], args[2]
            index = 2
        else:
            ids, vals = args[2:4]
            index = 3
        context = {}
        if index + 1 < len(args):
            context = args[index + 1]
        context = context or kwargs.get('context') or {}
    return cr, uid, ids, vals, context


def _special_wrapper(self, method, fields, *args, **kwargs):
    # Remove followers linked to old partner
    cr, uid, ids, vals, context = _get_args(self, args, kwargs)
    for field in fields:
        direct_field = field.split('.')[0]
        if direct_field in vals and ids:
            for record in self.pool[self._name].browse(cr, SUPERUSER_ID, ids, context):
                contacts = record.mapped(field)._get_contacts_to_notify()
                record.message_unsubscribe(contacts.ids)
    res = method(self, *args, **kwargs)
    # Add followers linked to new partner
    for field in fields:
        direct_field = field.split('.')[0]
        field_to_recompute = direct_field in self.pool.pure_function_fields
        if not field_to_recompute:
            for expr in self._fields[direct_field].depends:
                if expr.split('.')[0] in vals:
                    field_to_recompute = True
        if direct_field in vals or field_to_recompute:
            if hasattr(res, 'ids'):
                ids = res.ids
            if res and isinstance(res, (long, int)) and res is not True:
                ids = [res]
            _filter = lambda partner: self._name in [m.model for m in partner.notification_model_ids]
            for record in self.pool[self._name].browse(cr, SUPERUSER_ID, ids, context):
                contacts = record.mapped(field)._get_contacts_to_notify().filtered(_filter)
                record.message_subscribe(contacts.ids)
    return res


def add_followers(fields=None):
    fields = fields or ['partner_id']

    def decorator(create_or_write):

        def add_followers_wrapper(self, *args, **kwargs):
            cls = self.__class__
            if not hasattr(cls, '_follow_partner_fields'):
                cls._follow_partner_fields = set()
            cls._follow_partner_fields |= set(fields)
            return _special_wrapper(self, create_or_write, fields, *args, **kwargs)

        return add_followers_wrapper

    return decorator


def _add_followers(fields=None):
    fields = fields or ['partner_id']

    def add_followers_wrapper(self, *args, **kwargs):
        return _special_wrapper(self, add_followers_wrapper.origin, fields, *args, **kwargs)

    return add_followers_wrapper


def AddFollowers(fields=None):
    fields = fields or ['partner_id']

    def decorator(original_class):
        def _register_hook(self, cr):
            model_obj = self.pool.get(self._name)
            for method_name in ('create', 'write'):
                method = getattr(model_obj, method_name)
                if method.__name__ != 'add_followers_wrapper':
                    model_obj._patch_method(method_name, _add_followers(fields))
            return super(original_class, self)._register_hook(cr)

        original_class._follow_partner_fields = set(fields)
        original_class._register_hook = _register_hook
        return original_class
    return decorator
