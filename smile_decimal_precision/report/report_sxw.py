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

from odoo.report.report_sxw import rml_parse


def get_digits(self, obj=None, f=None, dp=None):
    d = DEFAULT_DIGITS = 2
    if dp:
        decimal_precision_obj = self.pool.get('decimal.precision')
        ids = decimal_precision_obj.search(self.cr, self.uid, [('name', '=', dp)])
        if ids:
            d = decimal_precision_obj.browse(self.cr, self.uid, ids)[0].display_digits
    elif obj and f:
        res_digits = getattr(obj._columns[f], 'digits', lambda x: 16, DEFAULT_DIGITS)
        if isinstance(res_digits, tuple):
            d = res_digits[1]
        else:
            d = res_digits(self.cr)[1]
    return d

rml_parse.get_digits = get_digits
