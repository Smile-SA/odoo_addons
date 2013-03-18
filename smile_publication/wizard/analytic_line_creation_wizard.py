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


class AccountAnalyticLineCreationWizard(orm.TransientModel):
    _name = 'account.analytic.line.creation_wizard'
    _description = 'Analytic line creation wizard'

    _columns = {
        'date_stop': fields.date('Generate publication numbers to invoice until', required=True),
    }

    _defaults = {
        'date_stop': lambda *a: time.strftime('%Y-%m-%d'),
    }

    def button_validate(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        wizard = self.browse(cr, uid, ids[0], context)
        context = context or {}
        account_ids = context.get('analytic_account_ids', [])
        return self.pool.get('account.analytic.account').generate_publication_lines(cr, uid, account_ids, wizard.date_stop, context)
