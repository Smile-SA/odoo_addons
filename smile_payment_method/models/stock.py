# -*- encoding: utf-8 -*-
##############################################################################
# Copyright (c) 2011 OpenERP Venezuela (http://openerp.com.ve)
# All Rights Reserved.
# Programmed by: Israel Fermín Montilla  <israel@openerp.com.ve>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
###############################################################################
from openerp import models, fields, api, exceptions
from openerp.tools.translate import _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    payment_method_id = fields.Many2one('account.payment.method',
                                       string='Payment Method')

    def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move, context=None):
        inv_vals = super(StockPicking, self)._get_invoice_vals(cr, uid, key, inv_type, journal_id, move, context=context)
        if move.picking_id:
            inv_vals.update({'payment_method_id': move.picking_id.payment_method_id.id,})
        return inv_vals


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _picking_assign(self, cr, uid, move_ids, procurement_group, location_from, location_to, context=None):
        res = super(StockMove, self)._picking_assign(cr, uid, move_ids, procurement_group, location_from, location_to, context=context)
        move = self.browse(cr, uid, move_ids[0], context=context)
        if move.picking_id:
            values = {
                'payment_method_id': move.procurement_id.sale_line_id.order_id.payment_method_id.id or False,
            }
            self.pool.get("stock.picking").write(cr, uid, move.picking_id.id, values, context=context)
        return res
