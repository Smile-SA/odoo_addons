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
from dateutil.relativedelta import relativedelta

from osv import osv, fields



class smile_activity_project(osv.osv):
    _name = 'smile.activity.project'


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


    ## Function fields

    def _get_month_range(self, cr, uid, ids, name, arg, context=None):
        """ Get a list of date objects set to the first day of each month covering date range of the project.
            XXX It may make sense later to link the project to a set of smile.activity.period objects instead. This proposition has to be carefully evaluated.
        """
        result = {}
        for project in self.browse(cr, uid, ids, context):
            month_range = []
            range_start = self._get_month_start(self._str_to_date(project.start_date))
            range_end   = self._get_month_end(self._str_to_date(project.end_date))
            date = range_start
            while date <= range_end:
                month_range.append(date)
                date = date + relativedelta(months=1)
            result[project.id] = month_range
        return result


    ## Fields definition

    _columns = {
        'name': fields.char('Name', size=32),
        'value_type': fields.selection([
            ('float', 'Float'),
            ('boolean', 'Boolean'),
            ], 'Value type', select=True, required=True),
        'required': fields.boolean('Required in report'),
        'start_date': fields.date('Start', required=True),
        'end_date': fields.date('End', required=True),
        # date_range is a requirement for the matrix widget
        'date_range': fields.function(_get_month_range, string="Month range", type='selection', readonly=True, method=True),
        }

    _defaults = {
        'value_type': 'float',
        'required': False,
        }

smile_activity_project()
