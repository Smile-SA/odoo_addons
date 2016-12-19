# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
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

from openerp import api, fields, models


class ProductOption(models.Model):
    _inherit = 'product.option'

    is_hidden_in_sale_order = fields.Boolean()
    is_hidden_in_customer_invoice = fields.Boolean()
    is_included_in_price = fields.Boolean(help="Check this if the price you use on the "
                                               "product and invoices includes this option.")

    _sql_constraints = [
        ('check_is_hidden_in_sale_order', "CHECK((is_hidden_in_sale_order IS NOT TRUE AND "
                                          "is_hidden_in_customer_invoice IS NOT TRUE) OR "
                                          "(quantity_type IN ('identical', 'fixed') AND is_mandatory))",
         'A option cannot is hidden if not mandatory and its quantity is not fixed or identical to the main product'),
        ('check_is_included_in_price', "CHECK(is_included_in_price IS NOT TRUE OR (quantity_type = 'identical' AND is_mandatory))",
         'A option cannot is included in price if not mandatory and its quantity is not identical to the main product'),
    ]

    @api.onchange('quantity_type')
    def _onchange_quantity_type(self):
        if self.quantity_type != 'identical':
            self.is_included_in_price = False
