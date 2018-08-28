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

from osv import osv
from tools.translate import _


class AccountVoucher(osv.osv):
    _inherit = 'account.voucher'

    def cancel_voucher(self, cr, uid, ids, context=None):
        context = context or {}
        if context.get('button_open_voucher_delinquency_wizard'):
            if isinstance(ids, (int, long)):
                ids = [ids]
            context['account_voucher_ids'] = ids
            return {
                'name': _('Unreconcile'),
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'account.voucher.reversal',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': context
            }
        context['reversal_date'] = time.strftime('%Y-%m-%d')
        context['voucher_cancellation'] = True
        return super(AccountVoucher, self).cancel_voucher(cr, uid, ids, context)
AccountVoucher()
