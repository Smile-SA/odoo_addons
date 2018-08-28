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

import time

from openerp.osv import orm, fields
from openerp.tools.translate import _


class AccountMoveLineReverse(orm.TransientModel):
    _name = "account.move.line.reverse"
    _description = "Create reversal of account move lines"

    _columns = {
        'account_id': fields.many2one('account.account', 'Destination Account', required=True),
        'date': fields.date('Reversal Date', required=True),
        'period_id': fields.many2one('account.period', 'Reversal Period'),
        'journal_id': fields.many2one('account.journal', 'Reversal Journal'),
        'move_line_prefix': fields.char('Items Name Prefix', size=32),
    }

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'move_line_prefix': lambda *a: 'REV -',
    }

    def action_reverse(self, cr, uid, wizard_id, context=None, post=True):
        action = {'type': 'ir.actions.act_window_close'}
        context = context or {}
        if context.get('active_ids'):
            if isinstance(wizard_id, list):
                wizard_id = wizard_id[0]
            wizard = self.browse(cr, uid, wizard_id, context)
            move_ids = []
            move_obj = self.pool.get('account.move')
            period_obj = self.pool.get('account.period')
            for line in self.pool.get('account.move.line').browse(cr, uid, context['active_ids'], context):
                if line.move_id.state != 'posted':
                    raise orm.except_orm(_('Error'), _('You cannot reverse a unposted journal item!'))
                context_copy = context and context.copy() or {}
                context_copy['company_id'] = line.company_id.id
                period_ids = period_obj.find(cr, uid, wizard.date, context_copy)
                move_vals = {
                    'name': wizard.move_line_prefix and "%s %s" % (wizard.move_line_prefix, line.move_id.name) or line.move_id.name,
                    'ref': line.ref,
                    'date': wizard.date,
                    'period_id': period_ids and period_ids[0] or False,
                    'journal_id': wizard.journal_id.id or line.journal_id.id,
                    'partner_id': line.partner_id.id,
                    'company_id': line.company_id.id,
                }
                first_line = move_vals.copy()
                first_line['debit'], first_line['credit'] = line.credit, line.debit
                first_line['account_id'] = line.account_id.id
                line_vals = [first_line]
                second_line = first_line.copy()
                second_line['debit'], second_line['credit'] = second_line['credit'], second_line['debit']
                second_line['account_id'] = wizard.account_id.id
                line_vals.append(second_line)
                move_vals['line_id'] = [(0, 0, vals) for vals in line_vals]
                move_id = move_obj.create(cr, uid, move_vals, context)
                if post:
                    move_obj.post(cr, uid, [move_id], context)
                move_ids.append(move_id)
            action_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'action_move_journal_line')
            action_id = action_ref and action_ref[1] or False
            action = self.pool.get('ir.actions.act_window').read(cr, uid, [action_id], context=context)[0]
            action['domain'] = str([('id', 'in', move_ids)])
            action['name'] = _('Reversal Entries')
        return action
