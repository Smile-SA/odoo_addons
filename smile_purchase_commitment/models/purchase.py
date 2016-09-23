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

from openerp import api, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _prepare_analytic_line(self, reverse=False):
        sign = reverse and 1 or -1
        order = self.order_id
        # Get default account used to generate supplier invoice
        account = self.product_id.product_tmpl_id.get_product_accounts().get('expense')
        return {
            'name': self.name,
            'product_id': self.product_id.id,
            'account_id': self.account_analytic_id.id,
            'unit_amount': sign * self.product_qty,
            'product_uom_id': self.product_uom.id,
            'amount': sign * order.currency_id.with_context(date=order.date_order
                                                            ).compute(self.price_subtotal, order.company_id.currency_id),
            'commitment_type': 'purchase',
            'commitment_account_id': account and account.id,
            'ref': self.order_id.name,
            'user_id': self._uid,
        }

    @api.one
    def _create_analytic_line(self, reverse=False):
        if self.account_analytic_id:
            vals = self._prepare_analytic_line(reverse=reverse)
            self.env['account.analytic.line'].create(vals)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        self.mapped('order_line')._create_analytic_line()
        return res

    @api.multi
    def button_cancel(self):
        res = super(PurchaseOrder, self).button_cancel()
        self.mapped('order_line')._create_analytic_line(reverse=True)
        return res
