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

from osv import osv

class AccountMove(osv.osv):
    _inherit = "account.move"

    def post(self, cr, uid, ids, context=None):
        if not ids:
            return True
        context = context or {}
        invoice = context.get('invoice')
        if invoice and invoice.behalf_of_id and self.validate(cr, uid, ids, context):
            move_obj = self.pool.get('account.move')
            period_obj = self.pool.get('account.period')
            src_accounts_mapping = dict([(mapping.account_src_id.id, mapping.account_dest_id.id) for mapping in invoice.behalf_of_id.account_src_ids])
            dest_accounts_mapping = dict([(mapping.account_src_id.id, mapping.account_dest_id.id) for mapping in invoice.behalf_of_id.account_dest_ids])
            for move in self.browse(cr, uid, ids, context):
                debit_line = [line for line in move.line_id if line.debit][0]
                new_debit_account_src_id = src_accounts_mapping.get(debit_line.account_id.id,
                    invoice.behalf_of_id.journal_src_id.default_debit_account_id.id)
                new_debit_account_dest_id = dest_accounts_mapping.get(debit_line.account_id.id,
                    dest_accounts_mapping.get(new_debit_account_src_id,
                        invoice.behalf_of_id.journal_dest_id.default_debit_account_id.id))

                debit_line.write({'account_id': new_debit_account_src_id}, context)
                move.write({'journal_id': invoice.behalf_of_id.journal_src_id.id,
                            'line_id': [(1, line.id, {'journal_id': invoice.behalf_of_id.journal_src_id.id}) for line in move.line_id],
                            }, context)

                context_copy = dict(context)
                context_copy['journal_id'] = invoice.behalf_of_id.journal_dest_id.id
                context_copy['period_id'] = period_obj.find(cr, uid, context={'company_id': invoice.behalf_of_id.company_dest_id.id})[0]
                ids.append(move_obj.create(cr, uid, {
                    'journal_id': context_copy['journal_id'],
                    'period_id': context_copy['period_id'],
                    'company_id': invoice.behalf_of_id.company_dest_id.id,
                    'line_id': [
                        (0, 0, {'name': '/',
                                'debit': move.amount, 'partner_id': move.partner_id.id,
                                'account_id': new_debit_account_dest_id}),
                        (0, 0, {'name': '/',
                                'credit': move.amount, 'partner_id': move.partner_id.id,
                                'account_id': invoice.behalf_of_id.journal_dest_id.default_credit_account_id.id}),
                    ],
                }, context_copy))
        return super(AccountMove, self).post(cr, uid, ids, context)
AccountMove()
