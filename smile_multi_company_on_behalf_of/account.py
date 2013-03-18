# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
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

import time

from osv import osv

from smile_account_fiscal_position_journal.account import FISCAL_POSITION_TYPES

FISCAL_POSITION_TYPES.append(('behalf', 'Billing on behalf of'))


class AccountMove(osv.osv):
    _inherit = "account.move"

    def post(self, cr, uid, ids, context=None):
        if not ids:
            return True
        context = context or {}
        invoice = context.get('invoice')
        if invoice and invoice.behalf_of_id and self.validate(cr, uid, ids, context):
            move_ids_to_post = ids[:]
            fiscal_position_obj = self.pool.get('account.fiscal.position')
            fiscal_position = invoice.behalf_of_id.fiscal_position_src_id
            cur_obj = self.pool.get('res.currency')
            for move in self.browse(cr, uid, ids, context):
                # Update move for the source company
                journal_id = fiscal_position_obj.map_journal(cr, uid, fiscal_position, move.journal_id.id, context)
                lines = []
                for line in move.line_id:
                    account_id = fiscal_position_obj.map_account(cr, uid, fiscal_position, line.account_id.id, context)
                    lines.append((1, line.id, {'account_id': account_id, 'journal_id': journal_id}))
                move.write({'journal_id': journal_id, 'line_id': lines}, context)  # TODO: test it in order to check if pass constraints
                # Create move for the destination company
                new_move_ids = invoice.behalf_of_id.account_model_dest_id.generate(context=context)
                for new_move in self.browse(cr, uid, new_move_ids, context):
                    if new_move.amount:
                        currency_src_id = move.company_id.currency_id.id
                        currency_dest_id = new_move.company_id.currency_id.id
                        vals = {'partner_id': move.partner_id.id}
                        for new_line in new_move.line_id:
                            vals['debit'], vals['credit'] = move.amount, 0.0
                            if new_line.credit:
                                vals['debit'], vals['credit'] = vals['credit'], vals['debit']
                            if currency_dest_id != currency_src_id:
                                amount = cur_obj.compute(cr, uid, currency_src_id, currency_dest_id,
                                                        vals['debit'] - vals['credit'], context={'date': time.strftime('%Y-%m-%d')})
                                vals.update({
                                    'currency_id': currency_src_id,
                                    'debit': vals['debit'] and amount or 0.0,
                                    'credit': vals['credit'] and amount * -1 or 0.0,
                                    'amount_currency': vals['debit'] - vals['credit'],
                                })
                            new_line.write(vals, context)
                        move_ids_to_post.append(new_move.id)
            ids = move_ids_to_post
        return super(AccountMove, self).post(cr, uid, ids, context)
AccountMove()
