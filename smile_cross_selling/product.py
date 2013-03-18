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

import openerp.addons.decimal_precision as dp
from openerp.osv import orm, fields


class ProductLink(orm.Model):
    _name = 'product.link'
    _description = "Linked Product"
    _rec_name = 'linked_product_id'

    _columns = {
        'product_id': fields.many2one('product.product', 'Main product', required=True, ondelete='cascade'),
        'linked_product_id': fields.many2one('product.product', 'Linked product', required=True, ondelete='cascade'),
        'active': fields.boolean('Active'),
        'quantity': fields.float('Quantity', digits_compute=dp.get_precision('Product UoS'), required=True),
        'price_type': fields.selection([('standard', 'Standard'), ('special', 'Special')], 'Price Type', required=True),
        'special_price': fields.float('Special Price', digits_compute=dp.get_precision('Product Price'), required=True),
        'mandatory': fields.boolean('Mandatory'),
    }

    _defaults = {
        'active': True,
        'quantity': 1.0,
        'price_type': 'standard',
        'special_price': 0.0,
    }


class ProductProduct(orm.Model):
    _inherit = 'product.product'

    _columns = {
        'product_link_ids': fields.one2many('product.link', 'product_id', 'Product links'),
    }
