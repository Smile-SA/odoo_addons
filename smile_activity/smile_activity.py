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
from matrix_field import matrix, matrix_read_patch, matrix_write_patch



class smile_activity_report(osv.osv):
    _name = 'smile.activity.report'

    #_order = "start_date"

    _columns = {
        'name': fields.char('Name', size=32),
        'period_id': fields.many2one('smile.activity.period', "Period", required=True),
        'start_date': fields.related('period_id', 'start_date', type='date', string="Start date", readonly=True),
        'end_date': fields.related('period_id', 'end_date', type='date', string="End date", readonly=True),
        'line_ids': fields.one2many('smile.activity.report.line', 'report_id', "Activity lines"),
        'matrix_line_ids': matrix(
            line_source='line_ids',
            line_type='smile.activity.report.line',
            cell_source='cell_ids',
            cell_type='smile.activity.report.cell',
            date_range_source='period_id',
            date_format='%d',
            resource_type='smile.activity.project',
            line_resource_source='project_id',
            string="Activity report lines",
            readonly=False,
            ),
        }


    ## Native methods

    def create(self, cr, uid, vals, context=None):
        report_id = super(smile_activity_report, self).create(cr, uid, vals, context)
        # Create default report lines
        for project_id in self.pool.get('smile.activity.project').search(cr, uid, [('required', '=', True)], context=context):
            vals = {
                'report_id': report_id,
                'project_id': project_id,
                }
            line_id = self.pool.get('smile.activity.report.line').create(cr, uid, vals, context)
        return report_id

    @matrix_read_patch
    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        return super(smile_activity_report, self).read(cr, uid, ids, fields, context, load)

    @matrix_write_patch
    def write(self, cr, uid, ids, vals, context=None):
        return super(smile_activity_report, self).write(cr, uid, ids, vals, context)


    ## Custom methods

    def update_cells(self, cr, uid, ids, context):
        """ This method maintain cells in sync with the period definition by
            removing out of range and inactive cells, and creating missing ones
            on each report lines.
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        outdated_cells = []
        for report in self.browse(cr, uid, ids, context):
            active_dates = [datetime.datetime.strptime(l.date, '%Y-%m-%d') for l in report.period_id.active_line_ids]
            for line in report.line_ids:
                # Get out of range cells
                outdated_cells += [cell.id for cell in line.cell_ids if datetime.datetime.strptime(cell.date, '%Y-%m-%d') not in active_dates]
                # Get missing cells
                existing_days = set([datetime.datetime.strptime(cell.date, '%Y-%m-%d') for cell in line.cell_ids])
                # Generate cells at missing dates
                for d in set(active_dates).difference(existing_days):
                    vals = {
                        'line_id': line.id,
                        'date': d,
                        }
                    self.pool.get('smile.activity.report.cell').create(cr, uid, vals, context)
        if outdated_cells:
            self.pool.get('smile.activity.report.cell').unlink(cr, uid, outdated_cells, context)
        return

smile_activity_report()



class smile_activity_report_line(osv.osv):
    _name = 'smile.activity.report.line'


    ## Function fields

    def _get_line_type(self, cr, uid, ids, name, arg, context=None):
        """ The line type is derived from the project it's attached to
        """
        result = {}
        for line in self.browse(cr, uid, ids, context):
            result[line.id] = line.project_id.value_type
        return result


    ## Fields definition

    _columns = {
        'name': fields.related('project_id', 'name', type='char', string='Project name', size=32, readonly=True),
        'report_id': fields.many2one('smile.activity.report', "Activity report", required=True, ondelete='cascade'),
        'project_id': fields.many2one('smile.activity.project', "Project", required=True),
        'cell_ids': fields.one2many('smile.activity.report.cell', 'line_id', "Cells"),
        'line_type': fields.function(_get_line_type, string="Line type", type='string', readonly=True, method=True),
        }


    ## Native methods

    def create(self, cr, uid, vals, context=None):
        line_id = super(smile_activity_report_line, self).create(cr, uid, vals, context)
        # Create default cells
        line = self.browse(cr, uid, line_id, context)
        self.generate_cells(cr, uid, line, context)
        return line_id


    ## Custom methods

    def generate_cells(self, cr, uid, line, context=None):
        """ This method generate all cells between the date range.
        """
        period_lines = line.report_id.period_id.active_line_ids
        vals = {
            'line_id': line.id
            }
        for period_line in period_lines:
            vals.update({'date': period_line.date})
            self.pool.get('smile.activity.report.cell').create(cr, uid, vals, context)
        return

smile_activity_report_line()



class smile_activity_report_cell(osv.osv):
    _name = 'smile.activity.report.cell'

    _order = "date"


    ## Function fields

    def _get_cell_value(self, cr, uid, ids, name, arg, context=None):
        """ Transform the quantity according the line type
        """
        result = {}
        for cell in self.browse(cr, uid, ids, context):
            val = cell.quantity
            if cell.line_id.line_type == 'boolean':
                val = (cell.quantity != 0) and True or False
            result[cell.id] = val
        return result


    ## Fields definition

    _columns = {
        'date': fields.date('Date', required=True),
        'quantity': fields.float('Quantity', required=True),
        'line_id': fields.many2one('smile.activity.report.line', "Activity report line", required=True, ondelete='cascade'),
        'cell_value': fields.function(_get_cell_value, string="Cell value", type='string', readonly=True, method=True),
        }

    _defaults = {
        'quantity': 0.0,
        }


    ## Constraints

    def _check_quantity(self, cr, uid, ids, context=None):
        for cell in self.browse(cr, uid, ids, context):
            if cell.quantity < 0:
                return False
        return True

    def _check_date(self, cr, uid, ids, context=None):
        for cell in self.browse(cr, uid, ids,context):
            date = datetime.datetime.strptime(cell.date, '%Y-%m-%d')
            report = cell.line_id.report_id
            start_date = datetime.datetime.strptime(report.start_date, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(report.end_date, '%Y-%m-%d')
            if date < start_date or date > end_date:
                return False
        return True

    def _check_duplicate(self, cr, uid, ids, context=None):
        for cell in self.browse(cr, uid, ids, context):
            if len(self.search(cr, uid, [('date', '=', cell.date), ('line_id', '=', cell.line_id.id)], context=context)) > 1:
                return False
        return True

    _constraints = [
        (_check_quantity, "Quantity can't be negative.", ['quantity']),
        (_check_date, "Cell date is out of the activity report date range.", ['date']),
        (_check_duplicate, "Two cells can't share the same date.", ['date']),
        ]

smile_activity_report_cell()
