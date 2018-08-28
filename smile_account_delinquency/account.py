# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

import netsvc
from osv import osv, fields


class AccountMove(osv.osv):
    _inherit = 'account.move'

    _columns = {
        'reversed': fields.boolean('Reversed', readonly=True),
    }

    def create_reversal(self, cr, uid, ids, reversal_date, reversal_ref_prefix=False, reversal_line_prefix=False, reconcile=True, context=None):
        self.write(cr, uid, ids, {'reversed': True}, context)
        reversal_ref_prefix = reversal_ref_prefix or 'REV-'
        return super(AccountMove, self).create_reversal(cr, uid, ids, reversal_date, reversal_ref_prefix, reversal_line_prefix, reconcile, context)

    def button_cancel(self, cr, uid, ids, context=None):
        move_ids_to_reverse = []
        move_ids_not_to_reverse = []
        for move in self.browse(cr, uid, ids, context=context):
            if move.journal_id.update_posted:
                move_ids_to_reverse.append(move.id)
            else:
                move_ids_not_to_reverse.append(move.id)
        if move_ids_to_reverse:
            context = context or {}
            invoice_obj = self.pool.get('account.invoice')
            invoice_to_cancel_ids = invoice_obj.search(cr, uid, [('move_id', 'in', move_ids_to_reverse)], context=context)
            voucher_obj = self.pool.get('account.voucher')
            voucher_to_cancel_ids = voucher_obj.search(cr, uid, [('move_id', 'in', move_ids_to_reverse)], context=context)
            if invoice_to_cancel_ids:
                wf_service = netsvc.LocalService("workflow")
                for invoice_id in invoice_to_cancel_ids:
                    wf_service.trg_validate(uid, 'account.invoice', invoice_id, 'invoice_cancel', cr)
            elif voucher_to_cancel_ids and not context.get('voucher_cancellation'):
                context['voucher_cancellation'] = True
                voucher_obj.cancel_voucher(cr, uid, voucher_to_cancel_ids, context)
            else:
                reversal_date = context.get('reversal_date') or time.strftime('%Y-%m-%d')
                reversed_move_ids = self.create_reversals(cr, uid, move_ids_to_reverse, reversal_date)
                self.button_validate(cr, uid, reversed_move_ids, context)
        if move_ids_not_to_reverse:
            super(AccountMove, self).button_cancel(cr, uid, move_ids_not_to_reverse, context)
        return True

    def unlink(self, cr, uid, ids, context=None, check=True):
        move_ids_to_unlink = []
        if isinstance(ids, (int, long)):
            ids = [ids]
        for move in self.read(cr, uid, ids, ['reversed'], context):
            if not move['reversed']:
                move_ids_to_unlink.append(move['id'])
        return super(AccountMove, self).unlink(cr, uid, move_ids_to_unlink, context, check)
AccountMove()
