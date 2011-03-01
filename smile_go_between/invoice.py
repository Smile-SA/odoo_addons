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

from osv import fields, osv
import time
from tools.translate import _

class account_invoice(osv.osv):
    _inherit = "account.invoice"
    
    def _get_invoice_line_ids2charge(self, cr, uid, ids):
        ret = []
        ret = self.pool.get('account.invoice.line').search(cr, uid, [('invoice_id', 'in', ids), ('invoice_line2charge_ok', '=', True), ('charged_ok', '=', False)])
        return ret
    
    def create_subcriber_purchase_order(self, cr, uid, ids, context=None):
        
        ret = []
        
        pricelist_obj = self.pool.get('product.pricelist')
        acc_pos_obj = self.pool.get('account.fiscal.position')
        prod_obj = self.pool.get('product.product')
        partner_obj = self.pool.get('res.partner')  
        
        ## récupérer les lignes de factures dont il faut payer une commission et qui ne sont pas toujours traitées
        invoice_line_ids = self._get_invoice_line_ids2charge(cr, uid, ids)
        if not invoice_line_ids:
            return ret

        ### Récupérer toutes les informations nécessaires
        cr.execute('select so.subscriber_id as supplier_id, r_sol_il.invoice_id as invoice_line_id, \
                                inv_line.product_id, inv_line.price_unit, inv_line.uos_id, \
                                inv_line.quantity, so.subscriber_pricelist_id as price_list_id, \
                                sol.name, r_sol_il.order_line_id as sol_id\
                        from sale_order_line_invoice_rel r_sol_il \
                            inner join sale_order_line sol on sol.id = r_sol_il.order_line_id\
                            inner join sale_order so on so.id = sol.order_id\
                            inner join account_invoice_line inv_line on inv_line.id = r_sol_il.invoice_id\
                        where (r_sol_il.invoice_id in %s)\
                        order by supplier_id', (tuple(invoice_line_ids),))
        
        res = cr.fetchall()
        partner_map = {}
        
        for x in res :
            if not x[0] in partner_map:
                partner_map[x[0]] = []
            
            data = {'invoice_line_id': x[1],
                    'product_id' :x[2],
                    'price_unit': x[3],
                    'uos_id': x[4],
                    'quantity' : x[5],
                    'pricelist_id' : x[6],
                    'description':x[7]}
            
            partner_map[x[0]].append(data)
        
        
        for partner_id in partner_map:
            pol_data_list = [] 
            partner = partner_obj.browse(cr, uid, partner_id)
            
            for line in partner_map[partner_id]:
                
                price = pricelist_obj.price_get(cr, uid, [line['pricelist_id']], line['product_id'], line['quantity'], False,
                                                {'uom': line['uos_id'],
                                                 'based_on_price':{line['product_id']:line['price_unit']}
                                                 })[line['pricelist_id']]

                data = {
                    'name': "Commission sur " + line['description'],
                    'product_qty': line['quantity'],
                    'product_id': line['product_id'],
                    'product_uom': line['uos_id'],
                    'price_unit': price,
                    'date_planned': time.strftime('%Y-%m-%d %H:%M:%S'),
                }

                product = prod_obj.browse(cr, uid, line['product_id'])
                taxes_ids = product.product_tmpl_id.supplier_taxes_id
                taxes = acc_pos_obj.map_tax(cr, uid, partner.property_account_position, taxes_ids)
                data.update({
                    'taxes_id': [(6, 0, taxes)]
                })
                
                pol_data_list.append(data)

            if not pol_data_list:
                continue
            
            ### create the purchase order
            address_id = partner_obj.address_get(cr, uid, [partner_id], ['delivery'])['delivery']
            pricelist_id = partner.property_product_pricelist_purchase.id
            
            warehouse_id = self.pool.get('purchase.order').default_get(cr, uid, ['warehouse_id'])['warehouse_id']
            
            res = self.pool.get('purchase.order').onchange_warehouse_id(cr, uid, [], warehouse_id)
            location_id = False
            if res and 'value' in res and 'location_id' in res['value'] :
                location_id = res['value']['location_id']
            else:
                raise osv.except_osv(_('Error'), _('Location not defined !'))
                
            purchase_id = self.pool.get('purchase.order').create(cr, uid, {
                'origin': "Généré automatiquement par le gestionnaire des commissions",
                'partner_id': partner_id,
                'partner_address_id': address_id,
                'pricelist_id': pricelist_id,
                'location_id': location_id,
                'company_id': self.pool.get('res.company')._company_default_get(cr, uid, 'purchase.order'),
                'fiscal_position': partner.property_account_position and partner.property_account_position.id or False
            })
            
            ret.append(purchase_id)
            
            for data in pol_data_list:
                data.update({
                    'order_id': purchase_id
                })
            
                pol_id = self.pool.get('purchase.order.line').create(cr, uid, data)
            
        self.pool.get('account.invoice.line').write(cr, uid, invoice_line_ids, {'charged_ok':True})  
            
        return ret
    
account_invoice()


class account_invoice_line(osv.osv):
    _inherit = "account.invoice.line"
    
    _columns = {
            'subscriber_invoice_line_id': fields.many2one('account.invoice.line', 'Subscriber invoice line', required=False, readonly=True),
            'invoice_line2charge_ok': fields.boolean('Invoice line to charge', required=False),
            'charged_ok': fields.boolean('Charged', required=False),

                    }
account_invoice_line()
