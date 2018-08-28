# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
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

import netsvc
from osv import osv, fields
from tools.translate import _


class AccountVoucher(osv.osv):
    _inherit = 'account.voucher'

    _columns = {
        'payment_id': fields.many2one('payment.order', 'Payment'),
    }

    def get_voucher_id(self, cr, uid, payment_id, partner_id, context):
        assert isinstance(payment_id, (int, long)), 'payment_id must be an integer!'
        assert isinstance(partner_id, (int, long)), 'partner_id must be an integer!'
        voucher_ids = self.search(cr, uid, [('payment_id', '=', payment_id), ('partner_id', '=', partner_id),
                                            ('state', '=', 'draft')], limit=1, context=context)
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

    def cancel_voucher(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        posted_voucher_ids = []
        voucher_to_post_ids = []
        for voucher in self.browse(cr, uid, ids, context):
            if voucher.state == 'posted':
                posted_voucher_ids.append(voucher.id)
            elif voucher.payment_id and voucher.payment_id.state != 'draft':
                raise osv.except_osv(_('Error'), _('You can not modify a voucher linked to a payment!'))
            else:
                voucher_to_post_ids.append(voucher.id)
        if posted_voucher_ids:
            super(AccountVoucher, self).cancel_voucher(cr, uid, posted_voucher_ids, context)
        if voucher_to_post_ids:
            wkf_service = netsvc.LocalService("workflow")
            for voucher_id in ids:
                wkf_service.trg_validate(uid, 'account.voucher', voucher_id, 'cancel_voucher', cr)
        return True

    def proforma_voucher(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for voucher in self.browse(cr, uid, ids, context):
            if voucher.payment_id and voucher.payment_id.state != 'draft':
                raise osv.except_osv(_('Error'), _('You can not modify a voucher linked to a payment!'))
        return super(AccountVoucher, self).proforma_voucher(cr, uid, ids, context)
AccountVoucher()
