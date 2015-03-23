# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Smile (<http://www.smile.fr>).
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

from openerp import fields


def clean_date(date):
    if date:
        if isinstance(date, basestring):
            try:
                date = fields.Date.from_string(date)
            except ValueError, e:
                raise Warning(repr(e))
    else:
        date = fields.Date.today()
    return date


def working_day_decorator():
    def working_day_wrapper(self, *args, **kwargs):
        self.pool['res.company'].clear_is_working_day_cache()
        return working_day_wrapper.origin(self, *args, **kwargs)
    return working_day_wrapper


def ClearWorkingDayCache(original_class):

    def _register_hook(self, cr):
        model_obj = self.pool.get(self._name)
        for method_name in ('create', 'write', 'unlink'):
            method = getattr(model_obj, method_name)
            if method.__name__ != 'working_day_wrapper':
                model_obj._patch_method(method_name, working_day_decorator())
        return super(original_class, self)._register_hook(cr)

    original_class._register_hook = _register_hook
    return original_class
