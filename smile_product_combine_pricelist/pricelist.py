# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
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

from osv import fields,osv



class product_pricelist(osv.osv):
    
    _inherit = 'product.pricelist'
   
    def price_get(self, cr, uid, ids, prod_id, qty, partner=None, context=None):
        
        ## surcharge de la méthode price get pour calculer impacter le prix du produit en cascade
        ## price = L1(L2(...(P))
        ## dans le cas d'un mix ça renvoi un prix
        
        
        ## Dans le cas d'un mix : 
        ## Le prix calculé est en fonction de la liste des listes de prix ids passées en paramètre
        ## on calcule le prmier prix issu de la première liste puis on repercute ce prix sur les suivantes.
        
        ## Si mix_price_list n'est pas définie on respect le calcul classique.
        
        if not context:
            context = {}
            
        res = {}
        if not context.get('mix_price_list',False):
            res = super(product_pricelist,self).price_get(cr, uid, ids, prod_id,qty,partner,context)
        
        else:
            if not isinstance(ids, list):
                ids = [ids]
            
            price = super(product_pricelist,self).price_get(cr,uid,[ids[0]],prod_id, qty or 1.0, partner, context)[ids[0]]
            
            for list_price_id in ids[1:] :
                context.update({'based_on_price':{prod_id:price}})
                price = super(product_pricelist,self).price_get(cr,uid,[list_price_id],prod_id, qty or 1.0, partner, context)[list_price_id]
                context.pop('based_on_price')
                        
            for id in ids :
                res[id] = price
            
            
        return res
    
    
product_pricelist()






