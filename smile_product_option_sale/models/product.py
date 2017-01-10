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
        ('check_is_hidden', "CHECK((is_hidden_in_sale_order IS NOT TRUE AND "
                            "is_hidden_in_customer_invoice IS NOT TRUE) OR "
                            "(quantity_type IN ('identical', 'fixed') AND is_mandatory))",
         'A option cannot is hidden if not mandatory or its quantity is not fixed or identical to the main product'),
        ('check_is_included_in_price', "CHECK(is_included_in_price IS NOT TRUE OR (quantity_type = 'identical' AND is_mandatory))",
         'A option cannot is included in price if not mandatory or its quantity is not identical to the main product'),
    ]

    @api.onchange('quantity_type')
    def _onchange_quantity_type(self):
        if self.quantity_type != 'identical':
            self.is_included_in_price = False


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.one
    def name_get(self):
        # Used on sale.order and account.invoice form view to display indentation on option lines
        product_id, name = super(ProductProduct, self).name_get()[0]
        if self._context.get('model_name') and self._context.get('line_ids'):
            model_name = self._context['model_name']
            if model_name not in self.env.registry:
                pass
            lines = self.env[model_name].browse([line_id for (_, line_id, _) in self._context['line_ids']])
            for line in lines.filtered(lambda line: line.parent_id):
                if self == line.product_id:
                    name = "%s%s" % (' + ' * line.tab_level, name)
                    break
        return product_id, name
