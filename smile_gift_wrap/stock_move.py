# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>). All Rights Reserved
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
from openerp.osv import orm, fields
from openerp.addons.stock.stock import stock_picking as super_stock_picking


class StockMove(orm.Model):
    _inherit = "stock.move"
    _columns = {
        'product_giftwrap_id': fields.many2one('product.product', 'Gift wrap'),
        }

    def _check_not_service_gift_product(self, cr, uid, ids, context=None):
        '''This constraint check if the product having a gift wrap "product_giftwrap_id" is not a service'''
        for line in self.browse(cr, uid, ids, context=context):
            if line.product_giftwrap_id and line.product_id.type == 'service':
                return False
        return True

    _constraints = [
        (_check_not_service_gift_product, 'The selected product is a service, it cant have a gift wrap',
         ['product_id', 'product_giftwrap_id']),
        ]

    def create(self, cr, uid, vals, context=None):
        if vals.get('sale_line_id'):
            sale_order_line = self.pool.get('sale.order.line').browse(cr, uid, vals['sale_line_id'])
            if sale_order_line:
                vals.update({'product_giftwrap_id': sale_order_line.product_giftwrap_id.id})
        move = super(StockMove, self).create(cr, uid, vals, context=context)
        return move


class StockPicking(orm.Model):
    _inherit = "stock.picking"
    _columns = {}

    def _invoice_hook(self, cursor, user, picking, invoice_id):
        '''Overcharge this method to avoid the creation of gift wrap line if the related wrapped product has not been
        sold yet'''

        sale_obj = self.pool.get('sale.order')
        order_line_obj = self.pool.get('sale.order.line')
        invoice_obj = self.pool.get('account.invoice')
        invoice_line_obj = self.pool.get('account.invoice.line')
        if picking.sale_id:
            sale_obj.write(cursor, user, [picking.sale_id.id], {
                'invoice_ids': [(4, invoice_id)],
            })
            for sale_line in picking.sale_id.order_line:
                if sale_line.product_id.type == 'service' and not sale_line.invoiced:
                    # Here is the added lines: Begin
                    if sale_line.wrapped_line_id and not sale_line.wrapped_line_id.invoice_lines:
                        continue
                    # End
                    vals = order_line_obj._prepare_order_line_invoice_line(cursor, user, sale_line, False)
                    vals['invoice_id'] = invoice_id
                    invoice_line_id = invoice_line_obj.create(cursor, user, vals)
                    order_line_obj.write(cursor, user, [sale_line.id], {
                        'invoice_lines': [(6, 0, [invoice_line_id])],
                    })
                    invoice_obj.button_compute(cursor, user, [invoice_id])
        return True
