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


class AccountFiscalPosition(osv.osv):
    _inherit = 'account.fiscal.position'

    _columns = {
        'company_id': fields.many2one('res.company', 'Company Source'),
        'company_dest_id': fields.many2one('res.company', 'Company Destination'),
    }

    def _check_company_ids(self, cr, uid, ids, context=None):
        for position in self.browse(cr, uid, ids, context):
            if position.type != 'standard' and not position.company_id:
                return False
        return True

    _constraints = [
        (_check_company_ids, 'Please indicate a company source and a company destination for each not standard fiscal position!',
         ['company_id', 'company_dest_id']),
    ]

AccountFiscalPosition()
