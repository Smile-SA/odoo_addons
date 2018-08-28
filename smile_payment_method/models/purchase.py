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


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    payment_method_id = fields.Many2one('account.payment.method',
                                       string='Payment Method')

    def action_invoice_create(self, cr, uid, ids, context=None):
        """ Set payment_method_id in the new invoice create from purchase order
        """
        res = super(PurchaseOrder, self).action_invoice_create(cr, uid,
                                                                  ids, context)
        inv_obj = self.pool.get('account.invoice')
        for order in self.browse(cr, uid, ids, context=context):
            inv_obj.write(cr, uid, res,
                          {'payment_method_id': order.payment_method_id and
                           order.payment_method_id.id},
                          context=context)

        return res

    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        '''Set of new payment_method_id in purchase order from partner'''
        partner = self.pool.get('res.partner')
        res = super(PurchaseOrder, self).onchange_partner_id(cr, uid, ids,
                                                                partner_id, context=context)

        if not partner_id:
            return {'value': {
                'fiscal_position': False,
                'payment_method_id': False,
            }}
        supplier = partner.browse(cr, uid, partner_id)
        res.get('value', {}).update({
            'payment_method_id': supplier.payment_method_suppliers_id and
            supplier.payment_method_suppliers_id.id or False})
        return res

    @api.multi
    def action_picking_create(self):
        res = super(PurchaseOrder, self).action_picking_create()
        for order in self:
            if order.payment_method_id:
                for picking in order.picking_ids:
                        picking.payment_method_id = order.payment_method_id.id
