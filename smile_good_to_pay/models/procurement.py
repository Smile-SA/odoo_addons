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


class ProcurementOrder(models.Model):
    _inherit = "procurement.order"

    location_id = fields.Many2one('stock.location', 'Procurement Location', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', required=True, help="Warehouse to consider for the route selection")
    approval_user_id = fields.Many2one('res.users', string='Approval user', default=lambda self: self.env.user)

    @api.model
    def create_procurement_purchase_order(self, procurement, po_vals, line_vals):
        """
        Add approval_user_id
        """
        po_vals.update({'approval_user_id': procurement.approval_user_id.id or False})
        return super(ProcurementOrder, self).create_procurement_purchase_order(procurement, po_vals, line_vals)
