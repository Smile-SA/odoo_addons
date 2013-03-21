# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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

from osv.orm import orm_template

from smile_decimal_precision import DecimalPrecision as dp


#native_fields_get = orm_template.fields_get
#
#
#def new_fields_get(self, cr, user, allfields=None, context=None, write_access=True):
#    res = native_fields_get(self, cr, user, allfields, context, write_access)
#    for field_name in res:
#        if field_name in self._columns:
#            field = self._columns[field_name]
#            if getattr(field, 'digits_compute', None) and field.digits_compute.func_closure:
#                application = field.digits_compute.func_closure[0].cell_contents
#                res[field_name]['digits'] = dp.get_display_precision(cr, user, application)
#    return res
#
#
#orm_template.fields_get = new_fields_get
