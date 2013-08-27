# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 CASDEN (<http://www.casden.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import re

from osv import fields, orm


class ResPartnerBank(orm.Model):
    _inherit = 'res.partner.bank'

    _columns = {
        'bank_bic': fields.char('BIC/SWIFT', size=11, required=False),
    }

    def _check_bic(self, cr, uid, ids, context=None):
        for account in self.browse(cr, uid, ids, context):
            if not account.bank_bic:
                continue
            bic_check = re.compile(r'^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$')  # INFO: ISO 9362:2009
            if not bic_check.match(account.bank_bic):
                return False
        return True

    _constraints = [
        (_check_bic, 'Incorrect BIC/SWIFT', ['bank_bic']),
    ]
