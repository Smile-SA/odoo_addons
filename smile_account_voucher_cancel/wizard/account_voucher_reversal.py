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

from osv import orm, fields


class AccountVoucherReversal(orm.TransientModel):
    _name = 'account.voucher.reversal'
    _description = 'Account Voucher Reversal'

    _columns = {
        'reversal_date': fields.date('Date of reversals', required=True, help="Enter the date of the reversal account moves."),
    }

    _defaults = {
        'reversal_date': time.strftime('%Y-%m-%d'),
    }

    def button_cancel_voucher(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'len(ids) != 1'
        context = context or {}
        del context['button_open_voucher_delinquency_wizard']
        context['reversal_date'] = self.read(cr, uid, ids[0], ['reversal_date'], context)['reversal_date']
        self.pool.get('account.voucher').cancel_voucher(cr, uid, context.get('account_voucher_ids', []), context)
        return {'type': 'ir.actions.act_window_close'}
