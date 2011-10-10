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

from datetime import datetime
from dateutil.relativedelta import relativedelta

from osv import osv
from tools.translate import _

class AccountFiscalyear(osv.osv):
    _inherit = 'account.fiscalyear'

    def create_analytic_periods(self, cr, uid, ids, context=None, interval=1):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for fiscalyear in self.browse(cr, uid, ids, context):
            if not fiscalyear.period_ids:
                raise osv.except_osv(_('Error'), _('Please, create general periods before analytic ones!'))
            date_start = datetime.strptime(fiscalyear.date_start, '%Y-%m-%d')
            while date_start.strftime('%Y-%m-%d') < fiscalyear.date_stop:
                date_stop = date_start + relativedelta(months=interval, days= -1)
                if date_stop.strftime('%Y-%m-%d') > fiscalyear.date_stop:
                    date_stop = datetime.strptime(fiscalyear.date_stop, '%Y-%m-%d')
                general_period_id = self.pool.get('account.period').search(cr, uid, [
                    ('date_start', '<=', date_start),
                    ('date_stop', '>=', date_stop),
                ], limit=1, context=context)
                if not general_period_id:
                    raise osv.except_osv(_('Error'), _('Analytic periods must be shorter than general ones!'))
                self.pool.get('account.analytic.period').create(cr, uid, {
                    'name': date_start.strftime('%m/%Y'),
                    'date_start': date_start.strftime('%Y-%m-%d'),
                    'date_stop': date_stop.strftime('%Y-%m-%d'),
                    'general_period_id': general_period_id[0],
                })
                date_start = date_start + relativedelta(months=interval)
        return True
AccountFiscalyear()
