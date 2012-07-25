# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http: //www.smile.fr>). All Rights Reserved
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
#    along with this program.  If not, see <http: //www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields


class AccountVoucher(osv.osv):
    _inherit = 'account.voucher'

    _columns = {
        'payment_id': fields.many2one('payment.order', 'Payment'),
    }

    def get_voucher_id(self, cr, uid, payment_id, partner_id, context):
        assert isinstance(payment_id, (int, long)), 'payment_id must be an integer!'
        assert isinstance(partner_id, (int, long)), 'partner_id must be an integer!'
        voucher_ids = self.search(cr, uid, [('payment_id', '=', payment_id), ('partner_id', '=', partner_id), ('state', '=', 'draft')], limit=1, context=context)
        if voucher_ids:
            voucher_id = voucher_ids[0]
        else:
            journal = self.pool.get('payment.order').browse(cr, uid, payment_id, context).journal_id
            voucher_id = self.create(cr, uid, {
                'type': 'payment',
                'partner_id': partner_id,
                'journal_id': journal.id,
                'account_id': journal.default_credit_account_id.id,
                'company_id': journal.company_id.id,
                'currency_id': journal.company_id.currency_id.id,
                'payment_id': payment_id,
            }, context)
        return voucher_id
AccountVoucher()
