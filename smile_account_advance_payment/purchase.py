# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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


class PurchaseOrder(orm.Model):
    _inherit = 'purchase.order'

    _columns = {
        'advance_payment_ids': fields.one2many('account.voucher', 'purchase_order_id', 'Advance Payments',
                                               domain=[('is_advance_payment', '=', True)],
                                               readonly=True, states={'approved': [('readonly', False)]},
                                               context={'default_is_advance_payment': True}),
    }

    def copy_data(self, cr, uid, order_id, default=None, context=None):
        default = default or {}
        default['advance_payment_ids'] = []
        return super(PurchaseOrder, self).copy_data(cr, uid, order_id, default, context=context)
