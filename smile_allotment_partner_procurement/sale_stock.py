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

from openerp import netsvc
from openerp.osv import orm, fields


class SaleOrder(orm.Model):
    _inherit = 'sale.order'

    _columns = {
        'picking_from_allotment_partner': fields.boolean('Generate a picking for each allotment partner'),
    }

    def _get_picking_from_allotment_partner(self, cr, uid, context=None):
        shop_id = self._get_default_shop(cr, uid, context)
        return self.pool.get('sale.shop').browse(cr, uid, shop_id, context).company_id.picking_from_allotment_partner

    _default = {
        'picking_from_allotment_partner': _get_picking_from_allotment_partner,
    }

    def onchange_shop_id(self, cr, uid, ids, shop_id, context=None):
        res = super(SaleOrder, self).onchange_shop_id(cr, uid, ids, shop_id, context)
        if shop_id:
            shop = self.pool.get('sale.shop').browse(cr, uid, shop_id, context)
            res.setdefault('value', {})['picking_from_allotment_partner'] = shop.company_id.picking_from_allotment_partner
        return res

    def _prepare_order_line_procurement(self, cr, uid, order, line, move_id, date_planned, context=None):
        res = super(SaleOrder, self)._prepare_order_line_procurement(cr, uid, order, line, move_id, date_planned, context)
        res['address_allotment_id'] = line.address_allotment_id.id or order.partner_shipping_id.id
        return res

    def _prepare_order_picking(self, cr, uid, order, context=None, address_allotment_id=False):
        pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out')
        return {
            'name': pick_name,
            'origin': order.name,
            'date': self.date_to_datetime(cr, uid, order.date_order, context),
            'type': 'out',
            'state': 'auto',
            'move_type': order.picking_policy,
            'sale_id': order.id,
            'partner_id': address_allotment_id or order.partner_shipping_id.id,  # Added by Smile
            'note': order.note,
            'invoice_state': order.order_policy == 'picking' and '2binvoiced' or 'none',
            'company_id': order.company_id.id,
        }

    def _create_pickings_and_procurements(self, cr, uid, order, order_lines, picking_id=False, context=None):
        move_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        procurement_obj = self.pool.get('procurement.order')
        proc_ids = []
        shipping_address_id = False  # Added by Smile

        for line in order_lines:
            if line.state == 'done':
                continue

            date_planned = self._get_date_planned(cr, uid, order, line, order.date_order, context=context)

            if line.product_id:
                if line.product_id.type in ('product', 'consu'):
                    # Modified by Smile #
                    picking_from_allotment_partner = line.order_id.company_id.picking_from_allotment_partner
                    new_shipping_address_id = picking_from_allotment_partner and line.address_allotment_id.id or order.partner_shipping_id.id
                    if not picking_id or shipping_address_id != new_shipping_address_id:
                        shipping_address_id = new_shipping_address_id
                        picking_id = picking_obj.create(cr, uid, self._prepare_order_picking(cr, uid, order, context, shipping_address_id))
                    #####################
                    move_id = move_obj.create(cr, uid, self._prepare_order_line_move(cr, uid, order, line, picking_id, date_planned, context=context))
                else:
                    move_id = False

                proc_vals = self._prepare_order_line_procurement(cr, uid, order, line, move_id, date_planned, context=context)
                proc_id = procurement_obj.create(cr, uid, proc_vals)
                proc_ids.append(proc_id)
                line.write({'procurement_id': proc_id})
                self.ship_recreate(cr, uid, order, line, move_id, proc_id)

        wf_service = netsvc.LocalService("workflow")
        if picking_id:
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
        for proc_id in proc_ids:
            wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)

        val = {}
        if order.state == 'shipping_except':
            val['state'] = 'progress'
            val['shipped'] = False

            if (order.order_policy == 'manual'):
                for line in order.order_line:
                    if (not line.invoiced) and (line.state not in ('cancel', 'draft')):
                        val['state'] = 'manual'
                        break
        order.write(val)
        return True
