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

from osv import orm


class AccountMove(orm.Model):
    _inherit = "account.move"

    def _get_line_id_to_reconcile(self, cr, uid, move, context=None):
        for line in move.line_id:
            if line.account_id.type in ('payable', 'receivable'):
                return line.id

    def _move_reversal(self, cr, uid, move, reversal_date, reversal_period_id=False, reversal_journal_id=False,
                       move_prefix=False, move_line_prefix=False, context=None, post_and_reconcile=False):
        if not reversal_journal_id and move.journal_id.reversal_journal_id:
            reversal_journal_id = move.journal_id.reversal_journal_id.id
        reversal_move_id = super(AccountMove, self)._move_reversal(cr, uid, move, reversal_date, reversal_period_id, reversal_journal_id,
                                                                   move_prefix, move_line_prefix, context)
        if post_and_reconcile:
            self.post(cr, uid, [reversal_move_id], context)
            reversal_move = self.browse(cr, uid, reversal_move_id, context)
            line_id_to_reconcile = self._get_line_id_to_reconcile(cr, uid, reversal_move, context)
            if line_id_to_reconcile:
                line_id = self._get_line_id_to_reconcile(cr, uid, move, context)
                self.pool.get('account.move.line').reconcile(cr, uid, [line_id_to_reconcile, line_id], context=context)
        return reversal_move_id

    def create_reversals(self, cr, uid, ids, reversal_date, reversal_period_id=False, reversal_journal_id=False,
                         move_prefix=False, move_line_prefix=False, context=None, post_and_reconcile=False):
        if isinstance(ids, (int, long)):
            ids = [ids]
        reversed_move_ids = []
        for src_move in self.browse(cr, uid, ids, context=context):
            if src_move.reversal_id:
                continue  # skip the reversal creation if already done
            reversal_move_id = self._move_reversal(cr, uid, src_move, reversal_date, reversal_period_id=reversal_period_id,
                                                   reversal_journal_id=reversal_journal_id, move_prefix=move_prefix,
                                                   move_line_prefix=move_line_prefix, context=context, post_and_reconcile=post_and_reconcile)
            if reversal_move_id:
                reversed_move_ids.append(reversal_move_id)
        return reversed_move_ids
