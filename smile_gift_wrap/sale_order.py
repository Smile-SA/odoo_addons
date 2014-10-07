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
from openerp.tools import ustr
from openerp.tools.translate import _


class SaleOrderLine(orm.Model):
    _inherit = "sale.order.line"
    _columns = {
        'product_giftwrap_id': fields.many2one('product.product', 'Gift wrap'),
        'wrapgift_so_line_id': fields.many2one('sale.order.line', 'Gift wrap price line'),
        'wrapped_line_id': fields.many2one('sale.order.line', 'Wrapped product line'),
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

    def copy(self, cr, uid, order_line_id, default=None, context=None):
        default = default or {}
        context = context or {}

        res = True
        order_line = self.browse(cr, uid, order_line_id, context=context)
        if order_line and not order_line.product_id.is_gift_ok:
            res = super(SaleOrderLine, self).copy(cr, uid, order_line_id, default, context)
        return res

    def copy_data(self, cr, uid, order_line_id, default=None, context=None):
        default = default or {}
        order_line = self.browse(cr, uid, order_line_id, context=context)
        if order_line and order_line.product_id.is_gift_ok:
            return

        default['wrapgift_so_line_id'] = False
        default['wrapped_line_id'] = False
        return super(SaleOrderLine, self).copy_data(cr, uid, order_line_id, default, context)

    def unlink(self, cr, uid, ids, context=None):
        '''- If the Wrapped product line is deleted we delete the related gift wrap price line
           - If we try to delete the product wrap gift line that is related to a gift product line we generate a restriction'''
        context = context or {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        for line in self.browse(cr, uid, ids, context):
            if line.wrapgift_so_line_id:
                wrapgift_so_line = line.wrapgift_so_line_id
                wrapgift_so_line.write({'wrapped_line_id': False})
                wrapgift_so_line.unlink()
            elif line.wrapped_line_id:
                raise orm.except_orm(_('Attention !'),
                                     _("you can't delete a product wrap gift price line if related to a wrapped product line"
                                       " you need to break the relation before or delete the wrapped product line"))

        return super(SaleOrderLine, self).unlink(cr, uid, ids, context)


class SaleOrder(orm.Model):
    _inherit = "sale.order"
    _columns = {}

    def treat_gift_lines(self, cr, uid, ids, context=None):
        context = context or {}

        if isinstance(ids, (int, long)):
            ids = [ids]
        order_line_obj = self.pool.get('sale.order.line')
        for order in self.browse(cr, uid, ids, context):
            for line in order.order_line:
                if line.product_giftwrap_id and not line.wrapgift_so_line_id:
                    name = line.product_giftwrap_id and line.product_giftwrap_id.name or '' 
                    name += " / "
                    name += line.product_id and line.product_id.name or ''
                    wrap_gift_line_id = order_line_obj.create(cr,
                                                              uid,
                                                              {'product_id': line.product_giftwrap_id.id,
                                                               'name': ustr(name),
                                                               'order_id': order.id,
                                                               'wrapped_line_id': line.id})

                    uos_qty = float(line.product_uos_qty)
                    if not uos_qty:
                        uos_qty = float(line.product_uom_qty)
                    lang = False
                    update_tax = True
                    flag = False
                    fiscal_position = order.fiscal_position and order.fiscal_position.id or False
                    res = order_line_obj.product_id_change(cr, uid, wrap_gift_line_id, order.pricelist_id.id,
                                                           line.product_giftwrap_id.id, line.product_uom_qty,
                                                           line.product_uom.id, uos_qty,
                                                           line.product_uos.id, ustr(line.name),
                                                           order.partner_id.id, lang, update_tax,
                                                           order.date_order, False,
                                                           fiscal_position, flag,
                                                           context)
                    name = line.product_giftwrap_id and line.product_giftwrap_id.name
                    name += " / " 
                    name += (line.product_id and line.product_id.name) or ""

                    line.write({'wrapgift_so_line_id': wrap_gift_line_id})
                    write_values = {'product_uos_qty': 1, 'name': ustr(name)}
                    for field in ['delay', 'th_weight', 'discount', 'product_uos', 'price_unit', 'product_packaging', 'type', 'tax_id']:
                        if res['value'].get(field):
                            if not field == 'tax_id':
                                write_values.update({field: res['value'][field]})
                            else:
                                write_values.update({field: [(6, 0, res['value'][field])]})
                    order_line_obj.write(cr, uid, [wrap_gift_line_id], write_values, context=context)
        return True

    def action_button_confirm(self, cr, uid, ids, context=None):
        self.treat_gift_lines(cr, uid, ids, context)
        return super(SaleOrder, self).action_button_confirm(cr, uid, ids, context=context)

    def button_dummy(self, cr, uid, ids, context=None):
        self.treat_gift_lines(cr, uid, ids, context)
        return super(SaleOrder, self).button_dummy(cr, uid, ids, context)
