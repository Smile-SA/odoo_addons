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


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = ['account.invoice', 'product.option.order']
    _order_line_field = 'invoice_line_ids'

    visible_line_ids = fields.One2many('account.invoice.line', 'invoice_id', 'Visible Invoice Lines',
                                       domain=[('is_hidden', '=', False)])


class AccountInvoiceLine(models.Model):
    _name = 'account.invoice.line'
    _inherit = ['account.invoice.line', 'product.option.order.line']
    _order_field = 'invoice_id'
    _qty_field = 'quantity'
    _uom_field = 'uom_id'

    parent_id = fields.Many2one('account.invoice.line', 'Main Line', ondelete='cascade', copy=False)
    child_ids = fields.One2many('account.invoice.line', 'parent_id', string='Options', context={'active_test': False})

    @api.one
    @api.constrains('quantity')
    def _check_qty(self):
        super(AccountInvoiceLine, self)._check_qty()

    _changed_fields = ['name', 'price_unit', 'account_id']

    @api.multi
    def _get_option_vals(self, option):
        vals = super(AccountInvoiceLine, self)._get_option_vals(option)
        vals['is_hidden'] = option.is_hidden_in_customer_invoice
        new_line = self.new(vals)
        new_line.invoice_id = self.invoice_id
        new_line._onchange_product_id()
        for field in self._changed_fields:
            if field not in vals and new_line[field]:
                vals[field] = new_line._fields[field].convert_to_write(new_line[field])
        return vals
