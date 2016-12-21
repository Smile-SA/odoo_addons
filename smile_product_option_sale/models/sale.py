# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
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

from openerp import api, fields, models


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'product.option.order']
    _order_line_field = 'order_line'

    visible_line_ids = fields.One2many('sale.order.line', 'order_id', 'Visible Order Lines',
                                       domain=[('is_hidden', '=', False)])

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        self = self.with_context(do_not_update_optional_lines=True)
        invoice_ids = super(SaleOrder, self).action_invoice_create(grouped, final)
        return invoice_ids


class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = ['sale.order.line', 'product.option.order.line']
    _order_field = 'order_id'
    _qty_field = 'product_uom_qty'
    _uom_field = 'product_uom'

    parent_id = fields.Many2one('sale.order.line', 'Main Line', ondelete='cascade', copy=False)
    child_ids = fields.One2many('sale.order.line', 'parent_id', string='Options', context={'active_test': False})
    is_hidden_in_customer_invoice = fields.Boolean(readonly=True)

    @api.one
    @api.constrains('product_uom_qty')
    def _check_qty(self):
        super(SaleOrderLine, self)._check_qty()

    @api.multi
    def _get_option_vals(self, option):
        vals = super(SaleOrderLine, self)._get_option_vals(option)
        vals.update({
            'is_hidden': option.is_hidden_in_sale_order,
            'is_hidden_in_customer_invoice': option.is_hidden_in_customer_invoice,
        })
        return vals

    @api.multi
    def _update_optional_lines_qty_delivered(self):
        for parent in self.filtered(lambda line: line.qty_delivered_updateable and line.product_uom_qty):
            factor = parent.qty_delivered / parent.product_uom_qty
            options = parent.child_ids.filtered(lambda child: child.is_hidden and child.qty_delivered_updateable)
            for option in options:
                option.qty_delivered = option.product_uom_qty * factor

    @api.multi
    def write(self, vals):
        res = super(SaleOrderLine, self).write(vals)
        if 'qty_delivered' in vals:
            self._update_optional_lines_qty_delivered()
        return res

    @api.multi
    def _prepare_invoice_line(self, qty):
        vals = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        vals.update({
            'parent_id': self.parent_id.invoice_lines.id,
            'quantity_type': self.quantity_type,
            'is_mandatory': self.is_mandatory,
            'is_hidden': self.is_hidden_in_customer_invoice,
            'is_included_in_price': self.is_included_in_price,
        })
        return vals
