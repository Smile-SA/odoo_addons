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
import tools
from tools.translate import _

class AnalyticPeriod(osv.osv):
    _name = 'account.analytic.period'
    _description = 'Analytic Period'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'code': fields.char('Code', size=12),
        'date_start': fields.date('Start of Period', required=True, states={'done':[('readonly', True)]}),
        'date_stop': fields.date('End of Period', required=True, states={'done':[('readonly', True)]}),
        'state': fields.selection([('draft', 'Opened'), ('done', 'Closed')], 'State', required=True, readonly=True),
        'general_period_id': fields.many2one('account.period', 'General Period', required=False), #not required because we want to allow different companies to use the periods
        'fiscalyear_id': fields.related('general_period_id', 'fiscalyear_id', string='Fiscal Year', type='many2one', relation='account.fiscalyear', readonly=True, store=True),
        'company_id': fields.related('fiscalyear_id', 'company_id', type='many2one', relation='res.company', string='Company', readonly=True, store=True),
    }

    _defaults = {
        'state': 'draft',
    }

    _order = "date_start"

    def _check_duration(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        period = self.browse(cr, uid, ids[0], context)
        if period.date_stop < period.date_start:
            return False
        if period.general_period_id \
        and (period.date_start < period.general_period_id.date_start \
        or period.date_stop > period.general_period_id.date_stop):
            return False            
        return True

    def _check_periods_overlap(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for period in self.browse(cr, uid, ids, context):
            domain = [
                ('id', '<>', period.id),
                ('date_start', '<=', period.date_stop),
                ('date_stop', '>=', period.date_start),
                ('company_id', 'in', period.company_id and [period.company_id.id, False] or [False]),
            ]
            if self.search(cr, uid, domain, context=context):
                return False
        return True

    _constraints = [
        (_check_duration, 'The duration of the period is invalid or the period dates are not in the scope of the account period!', ['date_start', 'date_stop']),
        (_check_periods_overlap, 'Some periods overlap!', ['date_start', 'date_stop']),
    ]

    def get_period_id_from_date(self, cr, uid, date=False, company_id=False, context=None):
        date = date or time.strftime('%Y-%m-%d')
        period_ids = self.search(cr, uid, [
            ('date_start', '<=', date),
            ('date_stop', '>=', date),
            ('company_id', 'in', [company_id, False])
        ], limit=1, context=context)
        if not period_ids:
            return 0
        if self.read(cr, uid, period_ids[0], ['state'], context)['state'] == 'done':
            raise osv.except_osv(_('Error'), _('You cannot pass a journal entry in a closed period!'))
        return period_ids[0]

    def _get_period_id(self, cr, uid, period_id, operator='>', state=None, context=None):
        if not isinstance(period_id, (int, long)):
            raise osv.except_osv(_('Error'), _('Please indicate a period id!'))
        period = self.read(cr, uid, period_id, ['date_start', 'company_id'], context)
        domain = [
            ('date_start', operator, period['date_start']),
            ('company_id', 'in', [period['company_id'] and period['company_id'][0], False]),
        ]
        if state:
            domain.append(('state', '=', state))
        order = 'date_start ' + (operator == '>' and 'asc' or 'desc')
        period_ids = self.search(cr, uid, domain, limit=1, order=order, context=context)
        return period_ids and period_ids[0] or 0

    @tools.cache()
    def get_previous_period_id(self, cr, uid, period_id, state=None, context=None):
        return self._get_period_id(cr, uid, period_id, '<', state, context)

    @tools.cache()
    def get_next_period_id(self, cr, uid, period_id, state=None, context=None):
        return self._get_period_id(cr, uid, period_id, '>', state, context)

    def button_close(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'done'}, context)

    def clear_caches(self, cr):
        self.get_previous_period_id.clear_cache(cr.dbname)
        self.get_next_period_id.clear_cache(cr.dbname)

    def create(self, cr, uid, vals, context=None):
        self.clear_caches(cr)
        return super(AnalyticPeriod, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        self.clear_caches(cr)
        if vals.get('state') == 'done':
            if isinstance(ids, (int, long)):
                ids = [ids]
            for period in self.read(cr, uid, ids, ['date_stop', 'company_id'], context):
                if self.search(cr, uid, [
                    ('date_stop', '<', period['date_stop']),
                    ('state', '=', 'draft'),
                    ('company_id', 'in', [period['company_id'] and period['company_id'][0], False]),
                ], context=context):
                    raise osv.except_osv(_('Warning!'), _('You cannot close a period if all previous periods are not closed!'))
        if vals.get('state') == 'draft':
            if isinstance(ids, (int, long)):
                ids = [ids]
            for period in self.read(cr, uid, ids, ['state', 'date_stop', 'company_id'], context):
                if period['state'] == 'done' and self.search(cr, uid, [
                    ('date_stop', '>', period['date_stop']),
                    ('state', '=', 'done'),
                    ('company_id', 'in', [period['company_id'] and period['company_id'][0], False]),
                ], context=context):
                    raise osv.except_osv(_('Warning!'), _('You cannot reopen a period if some next periods are closed!'))
        return super(AnalyticPeriod, self).write(cr, uid, ids, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        self.clear_caches(cr)
        return super(AnalyticPeriod, self).unlink(cr, uid, ids, context)

    def create_periods(self, cr, uid, global_date_start, global_date_stop, context=None, interval=1):
        context = context or {}
        date_start = datetime.strptime(global_date_start, '%Y-%m-%d')
        date_stop = datetime.strptime(global_date_stop, '%Y-%m-%d')
        while date_start < date_stop:
            date_stop = min(date_start + relativedelta(months=interval, days= -1), date_stop)
            vals = {
                'name': date_start.strftime('%m/%Y'),
                'code': date_start.strftime('%m/%Y'),
                'date_start': date_start.strftime('%Y-%m-%d'),
                'date_stop': date_stop.strftime('%Y-%m-%d'),
            }
            if context.get('fiscalyear_id'):
                general_period_id = self.pool.get('account.period').search(cr, uid, [
                    ('date_start', '<=', date_start.strftime('%Y-%m-%d')),
                    ('date_stop', '>=', date_stop.strftime('%Y-%m-%d')),
                    ('fiscalyear_id', '=', context['fiscalyear_id']),
                ], limit=1, context=context)
                if not general_period_id:
                    raise osv.except_osv(_('Error'), _('Analytic periods must be shorter than general ones!'))
                vals['general_period_id'] = general_period_id[0]
            self.pool.get('account.analytic.period').create(cr, uid, vals, context)
            date_start = date_start + relativedelta(months=interval)
        return True
AnalyticPeriod()

class AnalyticLine(osv.osv):
    _inherit = 'account.analytic.line'

    def _get_period_id(self, cr, uid, ids, name, arg, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = {}.fromkeys(ids, False)
        period_obj = self.pool.get('account.analytic.period')
        for line in self.read(cr, uid, ids, ['date', 'company_id'], context):
            res[line['id']] = period_obj.get_period_id_from_date(cr, uid, line['date'], line['company_id'] and line['company_id'][0], context)
        return res

    _columns = {
        'period_id': fields.function(_get_period_id, method=True, type='many2one', relation='account.analytic.period', string='Period', required=False, store={
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
        (_check_create_period, 'You cannot pass/update a journal entry in a closed period!', ['create_period_id']),
    ]
AnalyticLine()
