# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Smile. All Rights Reserved
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

import datetime
from dateutil.relativedelta import relativedelta

from osv import osv, fields
from tools.translate import _



class smile_activity_period(osv.osv):
    """ Activity periods are always 1 month long.

    """

    _name = 'smile.activity.period'

    _order = "start_date"


    ## Utility methods

    def _str_to_date(self, date):
        """ Transform string date to a proper date object
        """
        if not isinstance(date, (datetime.date, datetime.datetime)):
            date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        return date

    def _get_month_start(self, date):
        return datetime.date(date.year, date.month, 1)

    def _get_month_end(self, date):
        return (self._get_month_start(date) + relativedelta(months=1)) - datetime.timedelta(days=1)


    ## Function fields methods

    def _generate_name(self, start_date, end_date):
        """ Generate a human-friendly period name based on its dates
        """
        start_date = self._str_to_date(start_date)
        end_date = self._str_to_date(end_date)
        # TODO: Localize ?
        name = ['?? ???'] * 2
        if start_date:
            name[0] = start_date.strftime("%d %b")
        if end_date:
            name[1] = end_date.strftime("%d %b")
        return ' - '.join(name)

    def _get_name(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for period in self.browse(cr, uid, ids, context):
            res[period.id] = self._generate_name(period.start_date, period.end_date)
        return res

    def _get_month(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for period in self.browse(cr, uid, ids, context):
            if period.start_date:
                # TODO: Localize ?
                res[period.id] = self._str_to_date(period.start_date).strftime("%B")
        return res

    def _get_visible_line_ids(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for period in self.browse(cr, uid, ids, context):
            res[period.id] = self.pool.get('smile.activity.period.line').search(cr, uid, [('period_id', '=', period.id), ('visible_day', '=', True)], context=context)
        return res

    def _get_day_range(self, cr, uid, ids, name, arg, context=None):
        """ Get a list of date objects covering the given date range
        """
        result = {}
        for period in self.browse(cr, uid, ids, context):
            day_range = []
            start_date = self._str_to_date(period.start_date)
            end_date = self._str_to_date(period.end_date)
            date = start_date
            while date <= end_date:
                day_range.append(date)
                date = date + datetime.timedelta(days=1)
            result[period.id] = day_range
        return result

    def _get_visible_day_range(self, cr, uid, ids, name, arg, context=None):
        """ Get a list of visible date objects covering the given date range
        """
        res = {}
        for period in self.browse(cr, uid, ids, context):
            res[period.id] = [self._str_to_date(l.date) for l in period.visible_line_ids]
        return res


    ## Object fields definition

    _columns = {
        'name': fields.function(_get_name, method=True, type='char', size=100, string='Name', readonly=True),
        'start_date': fields.date('Start', required=True),
        'end_date': fields.date('End', required=True),
        'month_name': fields.function(_get_month, method=True, type='char', size=16, string='Month', readonly=True),
        'line_ids': fields.one2many('smile.activity.period.line', 'period_id', "Period lines"),
        'visible_line_ids': fields.function(_get_visible_line_ids, string="Visible lines", type='one2many', relation='smile.activity.period.line', method=True),
        'report_ids': fields.one2many('smile.activity.report', 'period_id', "Activity reports", readonly=True),
        # date_range is a requirement for the matrix widget
        'date_range': fields.function(_get_day_range, string="Day range", type='selection', readonly=True, method=True),
        # The visible_date_range is a matrix widget convention
        'visible_date_range': fields.function(_get_visible_day_range, string="Visible day range", type='selection', readonly=True, method=True),
        }

    _defaults = {
        'start_date': datetime.date(datetime.datetime.today().year, datetime.datetime.today().month, 1).strftime('%m/%d/%Y'), # Same behaviour as _get_month_start()
        'end_date': ((datetime.date(datetime.datetime.today().year, datetime.datetime.today().month, 1) + relativedelta(months=1)) - datetime.timedelta(days=1)).strftime('%m/%d/%Y'), # Same behaviour as _get_month_end()
        }


    ## Native methods

    def create(self, cr, uid, vals, context=None):
        period_id = super(smile_activity_period, self).create(cr, uid, vals, context)
        # Create default lines
        self.update_date_range(cr, uid, period_id, context)
        return period_id

    def write(self, cr, uid, ids, vals, context=None):
        today = datetime.date.today()
        for period in self.browse(cr, uid, ids, context):
            if self._str_to_date(period.end_date) < today:
                raise osv.except_osv(_('Error !'), _("Past periods are archived and can't be updated."))
        ret = super(smile_activity_period, self).write(cr, uid, ids, vals, context)
        # Always update lines
        self.update_date_range(cr, uid, ids, context)
        return ret

    def copy(self, cr, uid, id, default=None, context=None):
        raise osv.except_osv(_('Error !'), _("Periods can't be duplicated. They have to be generated from scratch."))

    def unlink(self, cr, uid, ids, context=None):
        for period in self.browse(cr, uid, ids, context):
            if len(period.report_ids):
                raise osv.except_osv(_('Error !'), _("Can't remove periods which have activity reports attached to it."))
        return super(smile_activity_period, self).unlink(cr, uid, ids, context)


    ## Constraints methods

    def _check_period_start(self, cr, uid, ids, context=None):
        today = datetime.date.today()
        for period in self.browse(cr, uid, ids, context):
            if self._str_to_date(period.start_date) < self._get_month_start(today):
                return False
        return True

    def _check_period_range(self, cr, uid, ids, context=None):
        for period in self.browse(cr, uid, ids, context):
            # Dates are YYYY-MM-DD strings, so can be compared as-is
            if period.start_date > period.end_date:
                return False
        return True

    def _check_period_lenght(self, cr, uid, ids, context=None):
        for period in self.browse(cr, uid, ids, context):
            start_date = self._str_to_date(period.start_date)
            end_date = self._str_to_date(period.end_date)
            if start_date != self._get_month_start(start_date) or end_date != self._get_month_end(start_date) or start_date.month != end_date.month or start_date.year != end_date.year:
                return False
        return True

    def _check_overlapping(self, cr, uid, ids, context=None):
        """ Check if any other period overlap the current one
        """
        for period in self.browse(cr, uid, ids, context):
            if len(self.pool.get('smile.activity.period').search(cr, uid, [('start_date', '<=', period.end_date), ('end_date', '>=', period.start_date), ('id', '!=', period.id)], context=context, limit=1)):
                return False
        return True

    _constraints = [
        (_check_period_start, "It doesn't make sense to create a period starting before the current month.", ['start_date']),
        (_check_period_range, "End date must be greater or equal to start date.", ['start_date', 'end_date']),
        (_check_period_lenght, "A period must cover the whole month.", ['start_date', 'end_date']),
        (_check_overlapping, "A period can't overlap another one.", ['start_date', 'end_date']),
        ]


    ## On change methods

    def onchange_start_date(self, cr, uid, ids, start_date, end_date):
        return {'value': {'name': self._generate_name(start_date, end_date)}}

    def onchange_end_date(self, cr, uid, ids, start_date, end_date):
        return {'value': {'name': self._generate_name(start_date, end_date)}}


    ## Custom methods

    def update_date_range(self, cr, uid, ids, context):
        """ Create and remove period lines to keep the date range in sync start date and stop date
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        for period in self.browse(cr, uid, ids, context):
            start_date = self._str_to_date(period.start_date)
            end_date = self._str_to_date(period.end_date)
            # Remove out of range lines
            outdated_lines = []
            for line in period.line_ids:
                date = self._str_to_date(period.end_date)
                if date < start_date or date > end_date:
                    outdated_lines.append(line.id)
            if outdated_lines:
                self.pool.get('smile.activity.period.line').unlink(cr, uid, outdated_lines, context)
            # Create missing lines to cover the whole period
            exiting_line_dates = [self._str_to_date(l.date) for l in period.line_ids]
            for date in [self._str_to_date(d) for d in period.date_range]:
                # Skip saturdays and sundays
                if date not in exiting_line_dates and date.weekday() not in [5, 6]:
                    vals = {
                        'date': date,
                        'period_id': period.id,
                        }
                    self.pool.get('smile.activity.period.line').create(cr, uid, vals, context)
        return

smile_activity_period()



class smile_activity_period_line(osv.osv):
    _name = 'smile.activity.period.line'

    _order = "date"


    ## Object fields definition

    _columns = {
        'date': fields.date('Date', required=True, readonly=True),
        'period_id': fields.many2one('smile.activity.period', "Period", required=True, readonly=True, ondelete='cascade'),
        'visible_day': fields.boolean('Visible day'),
        }

    _defaults = {
        'visible_day': True,
        }


    ## Constraints methods

    #def _check_overlapping(self, cr, uid, ids, context=None):
        #""" Check if any other date overlap the current one within the current period
        #"""
        #context.update({'active_test': False})
        #for line in self.browse(cr, uid, ids, context):
            #if len(self.search(cr, uid, [('date', '=', line.date), ('period_id', '=', line.period_id.id), ('id', '!=', line.id)], context=context, limit=1)):
                #return False
        #return True

    #_constraints = [
        ##(_check_overlapping, "Dates can't overlap within a period.", ['date', 'period_id']),
        #]

smile_activity_period_line()
