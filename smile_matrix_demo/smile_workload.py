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
import random

from osv import osv, fields
from smile_matrix_field.matrix_field import matrix, matrix_read_patch, matrix_write_patch, LINE_RENDERING_MODES



class smile_activity_workload(osv.osv):
    _name = 'smile.activity.workload'


    ## Function fields

    def _get_additional_line_ids(self, cr, uid, ids, name, arg, context=None):
        """ Randomly pick some lines to demonstrate the Matrix's additional_lines parameter
        """
        result = {}
        for workload in self.browse(cr, uid, ids, context):
            # Get even lines
            result[workload.id] = [l.id for l in workload.line_ids][::2]
        return result

    def _get_employee_filter_domain(self, cr, uid, ids, name, arg, context=None):
        """ Return a domain to filter employees.
            The implemented rule is absolutely arbitrary and is just there to demonstrate usage of matrix's dynamic_domain_property parameter.
        """
        result = {}
        for workload in self.browse(cr, uid, ids, context):
            # Only allow employees with IDs of the same parity of workload's start date
            odd_month = datetime.datetime.strptime(workload.start_date, '%Y-%m-%d').date().month % 2
            employee_ids = [i for i in self.pool.get('smile.activity.employee').search(cr, uid, [], context=context) if odd_month ^ (not i % 2)]
            result[workload.id] = [('id', 'in',  employee_ids)]
        return result


    ## Fields definition

    _columns = {
        'name': fields.char('Name', size=32),
        'project_id': fields.many2one('smile.activity.project', "Project", required=True),
        'start_date': fields.related('project_id', 'start_date', type='date', string="Start date", readonly=True),
        'end_date': fields.related('project_id', 'end_date', type='date', string="End date", readonly=True),
        'date_range': fields.related('project_id', 'date_range', type='selection', string="Period date range", readonly=True),
        'line_ids': fields.one2many('smile.activity.workload.line', 'workload_id', "Workload lines"),
        'additional_line_ids': fields.function(_get_additional_line_ids, string="Additional lines", type='one2many', relation='smile.activity.workload.line', readonly=True, method=True),
        'employee_filter': fields.function(_get_employee_filter_domain, string="Employee filter domain", type='string', readonly=True, method=True),
        'matrix': matrix(
            line_property='line_ids',
            line_type='smile.activity.workload.line',
            line_inverse_property='workload_id',
            cell_property='cell_ids',
            cell_type='smile.activity.workload.cell',
            cell_inverse_property='line_id',
            cell_value_property='quantity',
            cell_date_property='date',
            date_range_property='date_range',
            date_format='%m/%y',
            date_range_navigation = True,
            navigation_size = 12,
            highlight_date = datetime.date(datetime.date.today().year, datetime.date.today().month, 1),

            line_rendering_dynamic_property = 'line_rendering',
            increment_values = [-1, 0.0, 2.71, 3.14],

            tree_definition = [
                { 'line_property': 'profile_id',
                  'resource_type': 'smile.activity.profile',
                  'domain': [('name', 'not in', ['Consultant', 'Expert'])],
                },
                { 'line_property': 'employee_id',
                  'resource_type': 'smile.activity.employee',
                  'dynamic_domain_property': 'employee_filter',
                },
                ],
            # XXX 3-level resource test
            #tree_definition = [
                #{ 'line_property': 'profile_id',
                  #'resource_type': 'smile.activity.profile',
                #},
                #{ 'line_property': 'employee_id',
                  #'resource_type': 'smile.activity.employee',
                #},
                #{ 'line_property': 'workload_id',
                  #'resource_type': 'smile.activity.workload',
                #},
                #],
            additional_columns=[
                {'label': "Productivity", 'line_property': 'productivity_index', 'hide_value': True},
                {'label': "Performance" , 'line_property': 'performance_index' , 'hide_tree_totals': True},
                ],
            #additional_line_property='additional_line_ids',
            column_totals_warning_threshold=None,
            css_classes=['workload'],
            title="Workload lines",
            ),
        }


    ## Native methods

    @matrix_read_patch
    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        return super(smile_activity_workload, self).read(cr, uid, ids, fields, context, load)

    @matrix_write_patch()
    def write(self, cr, uid, ids, vals, context=None):
        return super(smile_activity_workload, self).write(cr, uid, ids, vals, context)


    ## Custom methods

    def modal_window_view(self, cr, uid, ids, context=None):
        return {
            'name':"View current form in modal window",
            'type': 'ir.actions.act_window',
            'res_model': 'smile.activity.workload',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.pool.get('ir.model.data').get_object_reference(cr, uid, 'smile_matrix_demo', 'view_smile_activity_workload_form')[::-1],
            'res_id': ids[0],
            'nodestroy': False,
            'target': 'new',
            'context': context,
            'toolbar': False,
        }


smile_activity_workload()



class smile_activity_workload_line(osv.osv):
    _name = 'smile.activity.workload.line'


    ## Function fields

    def _get_random_int(self, cr, uid, ids, name, arg, context=None):
        """ Get a random number between 0 and 100
        """
        result = {}
        for line in self.browse(cr, uid, ids, context):
            result[line.id] = random.randrange(0, 100)
        return result


    ## Fields definition

    _columns = {
        'name': fields.related('employee_id', 'name', type='char', string='Name', size=32, readonly=True),
        'line_rendering': fields.selection(LINE_RENDERING_MODES, 'Line rendering mode', select=True, required=True),
        'workload_id': fields.many2one('smile.activity.workload', "Workload", required=True, ondelete='cascade'),
        'profile_id': fields.many2one('smile.activity.profile', "Profile", required=False),
        'employee_id': fields.many2one('smile.activity.employee', "Employee", required=False),
        'cell_ids': fields.one2many('smile.activity.workload.cell', 'line_id', "Cells"),
        'performance_index': fields.function(_get_random_int, string="Performance index", type='float', readonly=True, method=True),
        'productivity_index': fields.function(_get_random_int, string="Productivity index", type='float', readonly=True, method=True),
        }

    _defaults = {
        'line_rendering': 'selection',
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
        #(_check_quantity, "Quantity can't be negative.", ['quantity']),
        (_check_date, "Cell date is out of the activity report date range.", ['date']),
        (_check_duplicate, "Two cells can't share the same date.", ['date']),
        ]

smile_activity_workload_cell()
