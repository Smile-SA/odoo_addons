# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>).
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

from osv import osv, fields

FISCAL_POSITION_TYPES = [('standard', 'Standard')]


class AccountFiscalPositionJournal(osv.osv):
    _name = 'account.fiscal.position.journal'
    _description = 'Journals Fiscal Position'
    _rec_name = 'position_id'

    _columns = {
        'position_id': fields.many2one('account.fiscal.position', 'Fiscal Position', required=True, ondelete='cascade'),
        'journal_src_id': fields.many2one('account.journal', 'Journal Source', required=True, ondelete='restrict'),
        'journal_dest_id': fields.many2one('account.journal', 'Journal Destination', required=True, ondelete='restrict')
    }

AccountFiscalPositionJournal()


class AccountFiscalPosition(osv.osv):
    _inherit = 'account.fiscal.position'

    _columns = {
        'type': fields.selection(FISCAL_POSITION_TYPES, 'Type', required=True),
        'journal_ids': fields.one2many('account.fiscal.position.journal', 'position_id', 'Journal Mapping'),
    }

    _defaults = {
        'type': 'standard',
    }

    def map_journal(self, cr, uid, fposition_id, journal_id, context=None):
        if not fposition_id:
            return journal_id
        for pos in fposition_id.journal_ids:
            if pos.journal_src_id.id == journal_id:
                journal_id = pos.journal_dest_id.id
                break
        return journal_id

AccountFiscalPosition()
