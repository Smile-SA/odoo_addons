# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Smile (<http://www.smile.fr>). All Rights Reserved
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

from odoo.addons.base.ir.ir_qweb.fields import FloatConverter


def record_to_html(self, record, field_name, options):
    if 'precision' not in options and 'decimal_precision' not in options:
        _, precision = record._fields[field_name].get_description(self.env)['digits'] or (None, None)
        options = dict(options, precision=precision)
    return super(FloatConverter, self).record_to_html(record, field_name, options)


FloatConverter.record_to_html = record_to_html
