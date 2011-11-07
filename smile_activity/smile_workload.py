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



class smile_activity_workload(osv.osv):
    _name = 'smile.activity.workload'

    _columns = {
        'name': fields.char('Name', size=32),
        'project_id': fields.many2one('smile.activity.project', "Project", required=True),
        'start_date': fields.related('project_id', 'start_date', type='date', string="Start date", readonly=True),
        'end_date': fields.related('project_id', 'end_date', type='date', string="End date", readonly=True),
        'line_ids': fields.one2many('smile.activity.workload.line', 'workload_id', "Workload lines"),
        'matrix_line_ids': matrix(
            line_property='line_ids',
            line_type='smile.activity.workload.line',
            line_inverse_property='workload_id',
            cell_property='cell_ids',
            cell_type='smile.activity.workload.cell',
            cell_value_property='quantity',
            date_range_property='project_id',
            date_format='%m/%y',
            resource_type='smile.activity.employee',
            line_resource_property='employee_id',
            group_by_property='profile_id',
            css_class=['workload'],
            experimental_slider=True,
            string="Workload lines",
            readonly=False,
            ),
        }


    ## Native methods

    @matrix_read_patch
    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        return super(smile_activity_workload, self).read(cr, uid, ids, fields, context, load)

    @matrix_write_patch
    def write(self, cr, uid, ids, vals, context=None):
        return super(smile_activity_workload, self).write(cr, uid, ids, vals, context)

smile_activity_workload()



class smile_activity_workload_line(osv.osv):
    _name = 'smile.activity.workload.line'

    _columns = {
        'name': fields.related('employee_id', 'name', type='char', string='Name', size=32, readonly=True),
        'workload_id': fields.many2one('smile.activity.workload', "Workload", required=True, ondelete='cascade'),
        #'profile_id': fields.many2one('smile.activity.profile', "Profile", required=False),
        'profile_id': fields.related('employee_id', 'profile_id', type='many2one', relation='smile.activity.profile', string="Profile", select=True, readonly=True),
        'employee_id': fields.many2one('smile.activity.employee', "Employee", required=False),
        'cell_ids': fields.one2many('smile.activity.workload.cell', 'line_id', "Cells"),
        }


    ## Native methods

    def create(self, cr, uid, vals, context=None):
        line_id = super(smile_activity_workload_line, self).create(cr, uid, vals, context)
        # Create default cells
        line = self.browse(cr, uid, line_id, context)
        self.generate_cells(cr, uid, line, context)
        return line_id


    ## Custom methods

    def generate_cells(self, cr, uid, line, context=None):
        """ This method generate all cells between the date range.
        """
        vals = {
            'line_id': line.id
            }
        for cell_date in line.workload_id.project_id.date_range:
            vals.update({'date': cell_date})
            self.pool.get('smile.activity.workload.cell').create(cr, uid, vals, context)
        return

smile_activity_workload_line()



class smile_activity_workload_cell(osv.osv):
    _name = 'smile.activity.workload.cell'

    _order = "date"


    ## Fields definition

    _columns = {
        'date': fields.date('Date', required=True),
        'quantity': fields.float('Quantity', required=True),
        'line_id': fields.many2one('smile.activity.workload.line', "Workload line", required=True, ondelete='cascade'),
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
            workload = cell.line_id.workload_id
            start_date = datetime.datetime.strptime(workload.start_date, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(workload.end_date, '%Y-%m-%d')
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

smile_activity_workload_cell()
