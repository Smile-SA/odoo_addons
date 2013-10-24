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

import decimal_precision as dp
from openerp.osv import orm, fields


class AccountVoucher(orm.Model):
    _inherit = 'account.voucher'

    def _is_credit_note(self, cr, uid, ids, prop, arg, context=None):
        res = {}
        for voucher in self.browse(cr, uid, ids, context):
            res[voucher.id] = {
                'is_credit_note': False,
                'amount_signed': voucher.amount,
            }
            amount = 0.0
            for line in voucher.line_ids:
                amount += line.amount * (line.type == 'cr' and -1.0 or 1.0)
            if amount < 0.0:
                res[voucher.id] = {
                    'is_credit_note': True,
                    'amount_signed': voucher.amount * -1.0,
                }
        return res

    _columns = {
        'is_credit_note': fields.function(_is_credit_note, method=True, type="boolean", string='Credit Note', store=True, multi='credit_note'),
        'amount_signed': fields.function(_is_credit_note, method=True, type='float', digits_compute=dp.get_precision('Account'),
                                         string='Total', store=True, multi='credit_note'),
    }

    def first_move_line_get(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        move_line_vals = super(AccountVoucher, self).first_move_line_get(cr, uid, voucher_id, move_id, company_currency, current_currency, context)
        if self.browse(cr, uid, voucher_id, context).is_credit_note:
            move_line_vals['debit'], move_line_vals['credit'] = move_line_vals['credit'], move_line_vals['debit']
        return move_line_vals

    def onchange_price(self, cr, uid, ids, line_ids, tax_id, partner_id=False, context=None):
        res = super(AccountVoucher, self).onchange_price(cr, uid, ids, line_ids, tax_id, partner_id, context)
        res['value']['is_credit_note'] = res['value']['amount'] < 0.0
        return res
