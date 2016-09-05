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

from odoo.fields import Field

from odoo.addons.smile_decimal_precision.models import DecimalPrecision as dp


native_get_description = Field.get_description


def new_get_description(self, env):
    desc = native_get_description(self, env)
    if getattr(self, '_digits', None) and callable(self._digits) and self._digits.func_closure:
        application = self._digits.func_closure[0].cell_contents
        desc['digits'] = dp.get_display_precision(env, application)
    return desc


Field.get_description = new_get_description
