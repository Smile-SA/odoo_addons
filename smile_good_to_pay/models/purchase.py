# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    approval_user_id = fields.Many2one('res.users', string='Approval user', default=lambda self: self.env.user)

    @api.model
    def _prepare_invoice(self, order, line_ids):
        """
            Override to update approval user in invoice
        """
        res = super(PurchaseOrder, self)._prepare_invoice(order, line_ids)
        res.update({'approval_user_id': order.approval_user_id.id})
        return res

    @api.multi
    def action_picking_create(self):
        """
            Override to update approval user in stock_picking
        """
        res = super(PurchaseOrder, self).action_picking_create()
        for order in self:
            if order.approval_user_id:
                for picking in order.picking_ids:
                        picking.approval_user_id = order.approval_user_id.id
        return res
