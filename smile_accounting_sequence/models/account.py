# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp import models
from openerp.osv import osv
from openerp.tools.translate import _


class AccountMove(models.Model):
    _inherit = 'account.move'

    def post(self, cr, uid, ids, context=None):
        """
        Override method =====> Add journal_id & period_id to next_by_id context
        """
        if context is None:
            context = {}
        invoice = context.get('invoice', False)
        valid_moves = self.validate(cr, uid, ids, context)

        if not valid_moves:
            raise osv.except_osv(_('Error!'), _('You cannot validate a non-balanced entry.' +
                                                '\nMake sure you have configured payment terms properly.' +
                                                '\nThe latest payment term line should be of the "Balance" type.'))
        obj_sequence = self.pool.get('ir.sequence')
        for move in self.browse(cr, uid, valid_moves, context=context):
            if move.name == '/':
                new_name = False
                journal = move.journal_id

                if invoice and invoice.internal_number:
                    new_name = invoice.internal_number
                else:
                    if journal.sequence_id:
                        c = {'fiscalyear_id': move.period_id.fiscalyear_id.id, 'period_id': move.period_id, 'journal_id': journal.id}
                        new_name = obj_sequence.next_by_id(cr, uid, journal.sequence_id.id, c)
                    else:
                        raise osv.except_osv(_('Error!'), _('Please define a sequence on the journal.'))
                if new_name:
                    self.write(cr, uid, [move.id], {'name': new_name})

        cr.execute("""UPDATE account_move
                      SET state=%s
                      WHERE id IN %s""", ('posted', tuple(valid_moves),))
        self.invalidate_cache(cr, uid, context=context)
        return True
