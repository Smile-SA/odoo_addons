# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010-2011 Smile (<http://smile.fr>).
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

from osv import osv, fields
from tools.translate import _
import netsvc


class product_product2(osv.osv):
    
    _inherit = 'product.product'
    
    def price_get(self, cr, uid, ids, ptype='list_price', context=None):
        
        if context is None:
            context = {}
        
        res = {}
        
        new_base_prices = {}
        if not 'based_on_price' in context:
            res =  super(product_product2,self).price_get(cr, uid, ids, ptype, context)
            
        else:
            
            new_base_prices = context.get('based_on_price',False)
            if not isinstance(new_base_prices,dict):
                return res
    
            if 'currency_id' in context:
                pricetype_obj = self.pool.get('product.price.type')
                price_type_id = pricetype_obj.search(cr, uid, [('field','=',ptype)])[0]
                price_type_currency_id = pricetype_obj.browse(cr,uid,price_type_id).currency_id.id
    
            res = {}
            product_uom_obj = self.pool.get('product.uom')
            for product in self.browse(cr, uid, ids, context=context):
                res[product.id] = new_base_prices[product.id] or 0.0
#                if ptype == 'list_price':
#                    res[product.id] = (res[product.id] * (product.price_margin or 1.0)) +\
#                            product.price_extra
                if 'uom' in context:
                    uom = product.uos_id or product.uom_id
                    res[product.id] = product_uom_obj._compute_price(cr, uid,
                            uom.id, res[product.id], context['uom'])
                # Convert from price_type currency to asked one
                if 'currency_id' in context:
                    # Take the price_type currency from the product field
                    # This is right cause a field cannot be in more than one currency
                    res[product.id] = self.pool.get('res.currency').compute(cr, uid, price_type_currency_id,
                        context['currency_id'], res[product.id],context=context)
    
        return res 

product_product2()
