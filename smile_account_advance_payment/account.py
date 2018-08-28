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

from openerp.osv import orm, fields


class AccountJournal(orm.Model):
    _inherit = 'account.journal'

    _columns = {
        'is_advance_journal': fields.boolean('Advance Journal'),
        'recovery_sequence_id': fields.many2one('ir.sequence', 'Recovery Entry Sequence'),
    }

    def _search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False, access_rights_uid=None):
        context = context or {}
        if context.get('filter_on_advance_journal') or context.get('filter_on_payment_journal'):
            if args and len(args) == 2 and args[0] == '&':
                args = [args[1]]
            cond = ('is_advance_journal', '=', context.get('filter_on_advance_journal', False))
            args = (args and ['&', cond] or [cond]) + args
        return super(AccountJournal, self)._search(cr, uid, args, offset, limit, order, context, count, access_rights_uid)
