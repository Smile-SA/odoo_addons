# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile. All Rights Reserved
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

from osv import osv, fields



class smile_period(osv.osv):
    _name = 'smile.period'

    _order = "start_date"

    # Period resolution in days. Here, each of our periods must be 7 days long
    PERIOD_RESOLUTION = 10

    def _str_to_date(self, date_str):
        """ Transform string date to a proper date object
        """
        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()

    def _generate_name(self, start_date, end_date):
        """ Generate a human-friendly period name based on its dates
        """
        start_date = self._str_to_date(start_date)
        end_date = self._str_to_date(end_date)
        # TODO: localize
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
                res[period.id] = self._str_to_date(period.start_date).strftime("%B")
        return res

    _columns = {
        'name': fields.function(_get_name, method=True, type='char', size=100, string='Name', readonly=True),
        'start_date': fields.date('Start', required=True),
        'end_date': fields.date('End', required=True),
        'month_name': fields.function(_get_month, method=True, type='char', size=16, string='Month', readonly=True),
        'line_ids': fields.one2many('smile.period.line', 'period_id', "Period lines"),
        }

    _defaults = {
        'start_date': datetime.datetime.today().strftime('%Y-%m-%d'),
        'end_date': (datetime.datetime.today() + datetime.timedelta(days=7)).strftime('%Y-%m-%d'),
        }


    ## Constraints methods

    def _check_period_start(self, cr, uid, ids, context=None):
        today = datetime.date.today()
        for period in self.browse(cr, uid, ids, context):
            start_date = self._str_to_date(period.start_date)
            this_monday = today - datetime.timedelta(days=today.weekday())
            if start_date < this_monday:
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
            if (end_date - start_date).days >= self.PERIOD_RESOLUTION:
                return False
        return True

    def _check_overlapping(self, cr, uid, ids, context=None):
        """ Check if any other period with the same supplier overlap the current one
        """
        for period in self.browse(cr, uid, ids, context):
            if len(self.pool.get('mrp.production_period').search(cr, uid, [('start_date', '<=', period.end_date), ('end_date', '>=', period.start_date), ('id', '!=', period.id), ('supplier_id', '=', period.supplier_id.id)], context=context, limit=1)):
                return False
        return True

    _constraints = [
        (_check_period_start, "It doesn't make sense to create a period starting before the current week.", ['start_date']),
        (_check_period_range, 'Stop date must be greater or equal to start date', ['start_date', 'end_date']),
        (_check_period_lenght, "A period can't be %s days or longer." % PERIOD_RESOLUTION, ['start_date', 'end_date']),
        #(_check_overlapping, "A period can't overlap another one having the same supplier", ['start_date', 'end_date', 'supplier_id']),
        ]


    ## Custom methods

    def get_date_range(self, project, day_delta=1):
        """ Get a list of date objects covering the given date range
        """
        date_range = []
        start_date = project.start_date
        end_date = project.end_date
        if not isinstance(start_date, (datetime.date, datetime.datetime)):
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        if not isinstance(end_date, (datetime.date, datetime.datetime)):
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        date = start_date
        while date <= end_date:
            date_range.append(date)
            date = date + datetime.timedelta(days=day_delta)
        return date_range

    def remove_outdated_cells(self, cr, uid, ids, vals, context):
        """ This method remove out of range cells on each sub lines
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        outdated_cells = []
        for project in self.browse(cr, uid, ids, context):
            start_date = datetime.datetime.strptime(project.start_date, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(project.end_date, '%Y-%m-%d')
            for line in project.line_ids:
                for cell in line.cell_ids:
                    date = datetime.datetime.strptime(cell.date, '%Y-%m-%d')
                    if date < start_date or date > end_date:
                        # Cell is out of range. Delete it.
                        outdated_cells.append(cell.id)
        if outdated_cells:
            self.pool.get('smile.project.line.cell').unlink(cr, uid, outdated_cells, context)
        return

smile_period()



class smile_period_line(osv.osv):
    """
    """
    _name = 'smile.period.line'

    _columns = {
        'date': fields.date('Date', required=True),
        'period_id': fields.many2one('smile.period', "Period", required=True, ondelete='cascade'),
        }

smile_period_line()
