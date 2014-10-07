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

{
    "name": "Box E-Commerce",
    "version": "1.0",
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "category": "Box E-Commerce",
    "description":
    """
    Sales :
        In : Dictionnary of data describing a sale order and its lines
        Out : Sale order confirmed in OpenERP
        
        Structure of the dictionnary to be sent
        
        SALE ORDER
        partner_id = order["customer_id"]
        partner_shipping_id = order["shipping_address_id"]
        partner_invoice_id = order["billing_address_id"]
        date_order = order["created_at"]    
        shop_id = order["store_id"]
        client_order_ref = order["ecommerce_sale_order_id"]
        payment_terms_id = order["payment_method"]        
        payment_reference = order["payment_reference"]    
        order_policy = order["order_policy"]    OPTIONAL selection manual/picking/prepaid -> picking by default
        picking_policy = order['picking_policy']    OPTIONAL selection direct/one -> one by default
        
        SALE ORDER LINE
        product_uom_qty = order["lines"][X]["qty"]
        price_unit = order["lines"][X]["price"]
        tax_id = order["lines"][X]["tax_id"]    MAPPING Mapping will probably be needed for each new project 
        name = order["lines"][X]["description"]
        gift = order["lines"][X]["gift"]        OPTIONAL bool
        product_id = order["lines"][X]["product_id"]    OPTIONAL
        discount = order["lines"][X]["discount"]    OPTIONAL
    """,

    "depends": ['magentoerpconnect', 'smile_payment_terms_auto', 'smile_gift_wrap'],
    "init_xml": [],
    "data":[
#         'views/static_mapping.xml',
        'data/data.xml',
        'data/payment.terms.partner.csv',
        'data/delivery.carrier.csv',
    ],
    "demo_xml": [],
    "installable": True,
    "active": False,
}
