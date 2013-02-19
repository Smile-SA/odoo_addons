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

from osv import osv


class Invoice(osv.osv):
    _inherit = 'account.invoice'

    def get_journal_from_fiscal_position(self, cr, uid, fiscal_position_id=False, journal_id=False):
        if fiscal_position_id and journal_id:
            fiscal_position = self.pool.get('account.fiscal.position').browse(cr, uid, fiscal_position_id)
            for fiscal_position_journal in fiscal_position.journal_ids:
                if fiscal_position_journal.journal_src_id.id == journal_id:
                    journal_id = fiscal_position_journal.journal_dest_id.id
                    break
        return journal_id

    def onchange_fiscal_position(self, cr, uid, ids, fiscal_position_id=False, journal_id=False):
        return {'value': {'journal_id': self.get_journal_from_fiscal_position(cr, uid, fiscal_position_id, journal_id)}}

    def onchange_journal_id(self, cr, uid, ids, journal_id=False, fiscal_position_id=False):
        res = super(Invoice, self).onchange_journal_id(cr, uid, ids, journal_id)
        res.setdefault('value', {})['journal_id'] = self.get_journal_from_fiscal_position(cr, uid, fiscal_position_id, journal_id)
        return res
Invoice()
