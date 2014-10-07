# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>). All Rights Reserved
#                       author cydef@smile.fr
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

from openerp.osv import (orm, fields)


class ECommercePaymentTerms(orm.Model):
    _inherit = 'payment.terms.partner'

    _sql_constraints = [
        ('unique_code', 'UNIQUE(code)', 'The code of the payment term must be unique!'),
    ]



class ECommerceShippingMode(orm.Model):
    _name = "ecommerce.shipping.mode"

    _columns = {
        "product_id": fields.many2one("product.product", "Product", required=True),
        "ecommerce_shipping_name": fields.char("E-Commerce Shipping Name", size=128),
        "ecommerce_shipping_key": fields.char("E-Commerce Shipping Key", size=128, required=True),
    }

    def get_ecommerce_ref(self, cr, uid, shipping_mode, context=None):
        mapping_id = self.search(cr, uid, [('product_id', '=', shipping_mode)], context=context)
        if mapping_id:
            mapping_record = self.browse(cr, uid, mapping_id[0], context=context)
            return mapping_record.ecommerce_shipping_key
        else:
            return None

    def get_oerp_ref(self, cr, uid, ecommerce_shipping_key, context=None):
        mapping_id = self.search(cr, uid, [('ecommerce_shipping_key', '=', ecommerce_shipping_key)], context=context)
        if mapping_id:
            mapping_record = self.browse(cr, uid, mapping_id[0], context=context)
            return mapping_record.product_id.id
        else:
            return None


# class ECommerceTaxesMap(orm.Model):
#     _name = "ecommerce.taxes.map"
#
#     _columns = {
#         "name": fields.char("Name", size=128),
#         "tax_ids": fields.many2many("account.tax", "ecommerce_mapping_tax_rel", "tax_mapping_id", "tax_id", string="Taxes", required=True),
#         "fiscal_position_id": fields.many2one("account.fiscal.position", "Fiscal Position"),
#         "ecommerce_tax_group": fields.char("E-Commerce Tax Group", size=128),
#         "ecommerce_key": fields.char("E-Commerce Key", size=128, required=True),
#     }
#
#     def get_ecommerce_ref(self, cr, uid, taxes, context=None):
#         mapping = self.search(cr, uid, [('tax_ids', 'in', taxes)], context=context)
#         # if we obtain several records, we need the mapping which has the same list of taxes
#         if mapping:
#             if len(mapping) > 1:
#                 tax_ids = self.read(cr, uid, mapping, ['tax_ids'], context=context)
#                 for index, tax in enumerate(tax_ids):
#                     if set(tax['tax_ids']) == set(taxes):
#                         mapping = [mapping[index]]
#                         break
#
#             mapping_record = self.browse(cr, uid, mapping, context=context)[0]
#             return mapping_record.ecommerce_key
#         else:
#             return None
#
#     def get_oerp_ref(self, cr, uid, ecommerce_key, context=None):
#         mapping_id = self.search(cr, uid, [('ecommerce_key', '=', ecommerce_key)], context=context)
#         if mapping_id:
#             mapping_record = self.browse(cr, uid, mapping_id[0], context=context)
#             return (mapping_record.tax_ids, mapping_record.fiscal_position_id.id)
#         else:
#             return (None, None)
