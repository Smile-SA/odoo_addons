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
    
class sale_order(osv.osv):
    _inherit = "sale.order"

    _columns = {
            'subscriber_id':fields.many2one('res.partner', 'Subscriber', required=False),
            'subscriber_pricelist_id':fields.many2one('product.pricelist', 'Subscriber Pricelist', required=False),
            'subscriber_invoice_ids': fields.many2many('account.invoice', 'sale_order_subscriber_invoice_rel', 'order_id', 'invoice_id', 'Subscriber Invoices', readonly=True, help="Invoices generated for ."),
                    }
    
    def _get_sol2mark_as2charge(self, cr, uid, ids):
        
        sale_order_line_ids = self.pool.get('sale.order.line').search(cr, uid, [('order_id', 'in', ids), ('got_from_subscriber_ok', '=', True)])
        cr.execute("select invoice_id from sale_order_line_invoice_rel where order_line_id in (" + ",".join([str(x) for x in sale_order_line_ids]) + ")")
        invoice_line_ids = []
        res = cr.fetchall()
        invoice_line_ids
        if res : 
            invoice_line_ids = [x[0] for x in res ]
        
        return invoice_line_ids
    
    def action_invoice_create(self, cr, uid, ids, grouped=False, states=['confirmed', 'done', 'exception'], date_inv=False, context=None):
        
        
        ret = super(sale_order, self).action_invoice_create(cr, uid, ids, grouped, states, date_inv, context)
        
        invoice_line_ids = self._get_sol2mark_as2charge(cr, uid, ids) 
        
        if invoice_line_ids:
            self.pool.get('account.invoice.line').write(cr, uid, invoice_line_ids, {'invoice_line2charge_ok':True})
        
        return ret
    
    def button_set_lines_got_from_subscriber_ok(self, cr, uid, ids, context=None):
        sol_ids = self.pool.get('sale.order.line').search(cr, uid, [('order_id', 'in', ids)])
        
        if sol_ids:
            sol_ids = self.pool.get('sale.order.line').write(cr, uid, sol_ids, {'got_from_subscriber_ok':True})
        return True
            
    def button_set_lines_got_from_subscriber_ko(self, cr, uid, ids, context=None):
        sol_ids = self.pool.get('sale.order.line').search(cr, uid, [('order_id', 'in', ids)])
        
        if sol_ids:
            sol_ids = self.pool.get('sale.order.line').write(cr, uid, sol_ids, {'got_from_subscriber_ok':False})
            
        return True
                
        
sale_order()


class sale_order_line(osv.osv):
    _inherit = "sale.order.line"

    _columns = {
            'got_from_subscriber_ok':fields.boolean('Got from subscriber', required=False),
                    }
    
    _defaults = {  
        'got_from_subscriber_ok': lambda * a: False,
        }
sale_order_line()
