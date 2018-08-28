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


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    payment_method_id = fields.Many2one('account.payment.method',
                                       string='Payment Method')

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        '''Overwrite this method to send the payment_method_id new to invoice '''

        res = super(SaleOrder, self)._prepare_invoice(cr, uid, order,
                                                         lines, context)
        res.update({'payment_method_id': order.payment_method_id and
                    order.payment_method_id.id
                    })

        return res

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        '''Overwrite this method to set payment_method_id new to sale order '''

        res = super(SaleOrder, self).onchange_partner_id(cr, uid, ids,
                                                            part, context)
        part = self.pool.get('res.partner').browse(cr, uid, part, context)

        payment_term = part.payment_method_customer_id and\
            part.payment_method_customer_id.id or False
        res.get('value', {}).update({
            'payment_method_id': payment_term,
        })

        return res
    