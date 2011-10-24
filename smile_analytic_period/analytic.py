
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

import time

from osv import osv, fields
from tools.translate import _

class AnalyticPeriod(osv.osv):
    _name = 'account.analytic.period'
    _description = 'Analytic Period'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'code': fields.char('Code', size=12),
        'date_start': fields.date('Start of Period', required=True, states={'done':[('readonly', True)]}),
        'date_stop': fields.date('End of Period', required=True, states={'done':[('readonly', True)]}),
        'state': fields.selection([('draft', 'Opened'), ('done', 'Closed')], 'State', required=True),
        'general_period_id': fields.many2one('account.period', 'General Period', required=True),
        'fiscalyear_id': fields.related('general_period_id', 'fiscalyear_id', string='Fiscal Year', type='many2one', relation='account.fiscalyear', readonly=True),
        'company_id': fields.related('fiscalyear_id', 'company_id', type='many2one', relation='res.company', string='Company', readonly=True),
    }

    _defaults = {
        'state': 'draft',
    }

    _order = "date_start"

    def _check_duration(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        period = self.browse(cr, uid, ids[0], context)
        if period.date_stop < period.date_start \
        or period.date_start < period.general_period_id.date_start \
        or period.date_stop > period.general_period_id.date_stop:
            return False            
        return True

    def _check_periods_overlap(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for period in self.browse(cr, uid, ids, context):
            domain = [
                ('id', '<>', period.id),
                '|', '|',
                '&', ('date_start', '>=', period.date_start), ('date_start', '<=', period.date_stop),
                '&', ('date_stop', '>=', period.date_start), ('date_stop', '<=', period.date_stop),
                '&', ('date_start', '<=', period.date_start), ('date_stop', '>=', period.date_stop),
            ]
            if self.search(cr, uid, domain, context=context):
                return False
        return True

    _constraints = [
        (_check_duration, 'The duration of the period is invalid or the period dates are not in the scope of the account period!', ['date_start', 'date_stop']),
        (_check_periods_overlap, 'Some periods overlap!', ['date_start', 'date_stop']),
    ]

    def get_period_id_from_date(self, cr, uid, date=False, context=None):
        date = date or time.strftime('%Y-%m-%d')
        period_id = self.search(cr, uid, [('date_start', '<=', date), ('date_stop', '>=', date)], limit=1, context=context)
        if not period_id:
            return False
        if self.read(cr, uid, period_id[0], ['state'], context)['state'] == 'done':
            raise osv.except_osv(_('Error'), _('You cannot pass a journal entry in a period closed!'))
        return period_id[0]

    def get_next_period_id(self, cr, uid, period_id, state=None, context=None):
        if not isinstance(period_id, (int, long)):
            raise osv.except_osv(_('Error'), _('Please indicate a period id!'))
        period = self.read(cr, uid, period_id, ['date_start'], context)
        domain = [('date_start', '>', period['date_start'])]
        if state:
            domain.append(('state', '=', state))
        next_period_ids = self.search(cr, uid, domain, limit=1, order='date_start asc', context=context)
        return next_period_ids and next_period_ids[0] or 0
AnalyticPeriod()

class AnalyticLine(osv.osv):
    _inherit = 'account.analytic.line'

    def _get_period_id(self, cr, uid, ids, name, arg, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = {}.fromkeys(ids, False)
        period_obj = self.pool.get('account.analytic.period')
        for line in self.read(cr, uid, ids, ['date'], context):
            res[line['id']] = period_obj.get_period_id_from_date(cr, uid, line['date'], context)
        return res

    _columns = {
        'period_id': fields.function(_get_period_id, method=True, type='many2one', relation='account.analytic.period', string='Period', store={
            'account.analytic.line': (lambda self, cr, uid, ids, context=None: ids, ['date'], 10),
        }),
        'create_period_id': fields.many2one('account.analytic.period', 'Create Period', domain=[('state', '!=', 'done')]),
    }

    def _get_default_period_id(self, cr, uid, context=None):
        return self.pool.get('account.analytic.period').get_period_id_from_date(cr, uid, context=context)

    _defaults = {
        'create_period_id': _get_default_period_id,
    }

    def _check_create_period(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for line in self.browse(cr, uid, ids, context):
            if line.create_period_id.state == 'done':
                return False
        return True

    _constraints = [
        (_check_create_period, 'You cannot pass/update a journal entry in a period closed!', ['create_period_id']),
    ]
AnalyticLine()
