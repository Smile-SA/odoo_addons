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


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    approval_user_id = fields.Many2one('res.users', string='Approval user')

    @api.model
    def _get_invoice_vals(self, key, inv_type, journal_id, origin):
        """
            Override to update approval user in invoice
        """
        res = super(StockPicking, self)._get_invoice_vals(key, inv_type, journal_id, origin)
        if inv_type in ('in_invoice', 'in_refund'):
            res.update({'approval_user_id': origin.picking_id.approval_user_id.id})
        return res
