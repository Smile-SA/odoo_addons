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

from osv import osv
from tools.translate import _


class AccountFiscalyear(osv.osv):
    _inherit = 'account.fiscalyear'

    def create_analytic_periods(self, cr, uid, ids, context=None, interval=1):
        context = context or {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        for fiscalyear in self.browse(cr, uid, ids, context):
            if not fiscalyear.period_ids:
                raise osv.except_osv(_('Error'), _('Please, create general periods before analytic ones!'))
            self.pool.get('account.analytic.period').create_periods(cr, uid, fiscalyear.date_start, fiscalyear.date_stop,
                                                                    context={'fiscalyear_id': fiscalyear.id})
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree, form',
            'res_model': 'account.analytic.period',
            'target': 'new',
            'context': context,
        }
AccountFiscalyear()
