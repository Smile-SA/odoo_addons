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

from osv import osv, fields


class AccountFiscalPositionJournalTemplate(osv.osv):
    _name = 'account.fiscal.position.journal.template'
    _description = 'Template for Journals Fiscal Position'
    _rec_name = 'position_id'

    _columns = {
        'position_id': fields.many2one('account.fiscal.position.template', 'Fiscal Position', required=True, ondelete='cascade'),
        'journal_src_id': fields.many2one('account.journal.template', 'Journal Source', required=True, ondelete='restrict'),
        'journal_dest_id': fields.many2one('account.journal.template', 'Journal Destination', required=True, ondelete='restrict'),
    }

AccountFiscalPositionJournalTemplate()


class AccountFiscalPositionTemplate(osv.osv):
    _inherit = 'account.fiscal.position.template'

    _columns = {
        'journal_ids': fields.one2many('account.fiscal.position.journal.template', 'position_id', 'Journal Mapping'),
    }

AccountFiscalPositionTemplate()
