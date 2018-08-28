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
import time

from osv import osv, fields
from tools.translate import _


class AnalyticInstaller(osv.osv_memory):
    _name = 'analytic.installer'
    _inherit = 'res.config.installer'

    _columns = {
        'period': fields.selection([('none', 'None'), ('global', 'Common for all companies'),
                                    ('specific', 'Specific to this company')], 'Periods', required=True),
        'company_id': fields.many2one('res.company', 'Company'),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year'),
        'date_start': fields.date('Start Date'),
        'date_stop': fields.date('End Date'),
    }

    def _default_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id and user.company_id.id or False

    _defaults = {
        'period': 'none',
        'date_start': time.strftime('%Y-01-01'),
        'date_stop': time.strftime('%Y-12-31'),
        'company_id': _default_company,
    }

    def onchange_fiscalyear_id(self, cr, uid, ids, fiscalyear_id):
        res = {'value': {'date_start': '', 'date_stop': ''}}
        if fiscalyear_id:
            fiscalyear = self.pool.get('account.fiscalyear').read(cr, uid, fiscalyear_id, ['date_start', 'date_stop'])
            res['value'].update({'date_start': fiscalyear['date_start'], 'date_stop': fiscalyear['date_stop']})
        return res

    def onchange_date_start(self, cr, uid, ids, date_start=False):
        if date_start:
            date_start = datetime.strptime(date_start, "%Y-%m-%d")
            date_stop = (date_start + relativedelta(months=12)) - relativedelta(days=1)
            return {'value': {'date_stop': date_stop.strftime('%Y-%m-%d')}}
        return {}

    def execute(self, cr, uid, ids, context=None):
        super(AnalyticInstaller, self).execute(cr, uid, ids, context)
        for wizard in self.read(cr, uid, ids, context=context, load='_classic_write'):
            if wizard['period'] != 'none':
                date_start = wizard.get('date_start')
                date_stop = wizard.get('date_stop')
                fiscalyear_id = False
                if wizard.get('fiscalyear_id'):
                    fiscalyear_id = wizard['fiscalyear_id']
                    fiscalyear = self.pool.get('account.fiscalyear').read(cr, uid, fiscalyear_id, ['date_start', 'date_stop'], context)
                    date_start = fiscalyear['date_start']
                    date_stop = fiscalyear['date_stop']
                if date_start > date_stop:
                    raise osv.except_osv(_('Warning!'), _('Start date must be prior than end date!'))
                self.pool.get('account.analytic.period').create_periods(cr, uid, date_start, date_stop, {'fiscalyear_id': fiscalyear_id})
AnalyticInstaller()
