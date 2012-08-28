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
import random
import os

from osv import osv, fields
from smile_matrix_field.matrix_field import matrix, matrix_read_patch, matrix_write_patch, LINE_RENDERING_MODES



class smile_activity_report(osv.osv):
    _name = 'smile.activity.report'

    #_order = "start_date"


    ## Function fields

    def _is_matrix_readonly(self, cr, uid, ids, name, arg, context=None):
        """ Dynamiccaly set the readonly property of the matrix
        """
        result = {}
        for report in self.browse(cr, uid, ids, context):
            result[report.id] = random.randrange(0, 2)
        return result


    ## Fields definition

    _columns = {
        'name': fields.char('Name', size=32),
        'period_id': fields.many2one('smile.activity.period', "Period", required=True),
        'start_date': fields.related('period_id', 'start_date', type='date', string="Start date", readonly=True),
        'end_date': fields.related('period_id', 'end_date', type='date', string="End date", readonly=True),
        'line_ids': fields.one2many('smile.activity.report.line', 'report_id', "Activity lines"),
        'date_range': fields.related('period_id', 'date_range', type='selection', string="Period date range", readonly=True),
        'visible_date_range': fields.related('period_id', 'visible_date_range', type='selection', string="Period visible date range", readonly=True),
        'is_matrix_readonly': fields.function(_is_matrix_readonly, string="Matrix dynamic readonly property", type='boolean', readonly=True, method=True),
        'matrix_1': matrix(
            line_property           = 'line_ids',
            line_type               = 'smile.activity.report.line',
            line_inverse_property   = 'report_id',
            line_removable_property = 'removable',
            tree_definition = [
                { 'line_property': 'project_id',
                  'resource_type': 'smile.activity.project',
                },
                ],
            #default_line_rendering          = 'selection',
            line_rendering_dynamic_property = 'line_rendering',
            increment_values             = [-1, 0.0, 2.71, 3.14],
            cell_property         = 'cell_ids',
            cell_type             = 'smile.activity.report.cell',
            cell_inverse_property = 'line_id',
            cell_value_property   = 'cell_value',
            cell_date_property    = 'date',
            cell_value_range      = 'cell_value_range',
            date_range_property        = 'date_range',
            visible_date_range_property = 'visible_date_range',
            date_format                = '%d',
            navigation = True,
            navigation_start = 10,
            additional_columns = [
                {'label': "Productivity", 'line_property': "productivity_index", 'position': 'left'},
                {'label': "Performance", 'line_property': "performance_index"},
                ],
            column_totals_warning_threshold = 1.0,
            title = "Activity report lines",
            css_classes = ['my_custom_css', ],
            custom_css = """
                /* Use a nice shade of blue for the total line of that matrix */
                .matrix.my_custom_css .total td,
                .matrix.my_custom_css .total th {
                    background-color: #abd4ff;
                }
                """,
            custom_js = open(os.path.join(os.path.dirname(__file__), 'custom.js'), 'r').read(),
            ),
        # Test multiple matrix widget
        'matrix_2': matrix(
            line_property           = 'line_ids',
            line_type               = 'smile.activity.report.line',
            line_inverse_property   = 'report_id',
            tree_definition = [
                { 'line_property': 'project_id',
                  'resource_type': 'smile.activity.project',
                },
                ],
            default_line_rendering = 'increment',
            cell_property          = 'cell_ids',
            cell_type              = 'smile.activity.report.cell',
            cell_inverse_property  = 'line_id',
            cell_value_property    = 'cell_value',
            cell_date_property     = 'date',
            cell_visible_property   = 'cell_value',
            #cell_readonly_property = 'read_only',
            date_range_property = 'date_range',
            date_format         = '%d',
            #hide_line_title          = True,
            #hide_remove_line_buttons = True,
            #hide_column_totals       = True,
            #hide_line_totals         = True,
            navigation = True,
            read_only = 'is_matrix_readonly',
            title = "Activity report lines 2",
            ),
        }


    ## Native methods

    def create(self, cr, uid, vals, context=None):
        report_id = super(smile_activity_report, self).create(cr, uid, vals, context)
        # Create default report lines
        for project_id in self.pool.get('smile.activity.project').search(cr, uid, [('add_by_default', '=', True)], context=context):
            vals = {
                'report_id': report_id,
                'project_id': project_id,
                }
            line_id = self.pool.get('smile.activity.report.line').create(cr, uid, vals, context)
        return report_id

    @matrix_read_patch
    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        return super(smile_activity_report, self).read(cr, uid, ids, fields, context, load)

    @matrix_write_patch()
    def write(self, cr, uid, ids, vals, context=None):
        return super(smile_activity_report, self).write(cr, uid, ids, vals, context)

smile_activity_report()



class smile_activity_report_line(osv.osv):
    _name = 'smile.activity.report.line'


    ## Function fields

    def _get_random_boolean(self, cr, uid, ids, name, arg, context=None):
        """ Get a random boolean
        """
        result = {}
        for line in self.browse(cr, uid, ids, context):
            result[line.id] = random.randrange(0, 2)
        return result

    def _get_random_integer(self, cr, uid, ids, name, arg, context=None):
        """ Get a random number between 0 and 99
        """
        result = {}
        for line in self.browse(cr, uid, ids, context):
            result[line.id] = random.randrange(0, 100)
        return result


    ## Fields definition

    _columns = {
        'report_id': fields.many2one('smile.activity.report', "Activity report", required=True, ondelete='cascade'),
        'project_id': fields.many2one('smile.activity.project', "Project", required=True),
        'cell_ids': fields.one2many('smile.activity.report.cell', 'line_id', "Cells"),
        'removable': fields.function(_get_random_boolean, string="Removable line", type='boolean', readonly=True, method=True),
        'performance_index': fields.function(_get_random_integer, string="Performance index", type='float', readonly=True, method=True),
        'productivity_index': fields.function(_get_random_integer, string="Productivity index", type='float', readonly=True, method=True),
        # Line name and rendering mode are derived from the project it's attached to
        'name': fields.related('project_id', 'name', type='char', string='Project name', size=32, readonly=True),
        'line_rendering': fields.related('project_id', 'value_type', type='selection', selection=LINE_RENDERING_MODES, string='Line rendering mode', readonly=True),
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
        period_lines = line.report_id.period_id.visible_line_ids
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
        """ Transform the quantity according the line rendering mode
        """
        result = {}
        for cell in self.browse(cr, uid, ids, context):
            val = cell.quantity
            if cell.line_id.line_rendering == 'boolean':
                val = (cell.quantity != 0) and True or False
            result[cell.id] = val
        return result

    def _set_cell_value(self, cr, uid, ids, name, value, arg, context=None):
        """ Transform and save the cell value to the quantity
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        for cell in self.browse(cr, uid, ids, context=context):
            # Float conversion
            if type(value) is type(''):
                value = float(value)
            self.write(cr, uid, cell.id, {'quantity': value}, context)
        return True

    def _get_cell_value_range(self, cr, uid, ids, name, value, arg, context=None):
        """ Return a random range a cell value is allowed to take
        """
        result = {}
        for cell in self.browse(cr, uid, ids, context):
            # Pick a random range to demonstrate the dynamic capability
            if random.randrange(0, 2):
                value_range = [0, 1, 2, 3]
            else:
                value_range = [-4, -3, -2, -1]
            result[cell.id] = value_range
        return result


    ## Fields definition

    _columns = {
        'date': fields.date('Date', required=True),
        'quantity': fields.float('Quantity', required=True),
        'line_id': fields.many2one('smile.activity.report.line', "Activity report line", required=True, ondelete='cascade'),
        'active': fields.boolean("Active"),
        'read_only': fields.boolean("Read-only"),
        # cell_value is a proxy of quantity that is transforming the value according the line_rendering mode
        'cell_value': fields.function(_get_cell_value, fnct_inv=_set_cell_value, string="Cell value", type='string', readonly=True, method=True),
        'cell_value_range': fields.function(_get_cell_value_range, string="Cell value range", type='selection', readonly=True, method=True),
        }

    _defaults = {
        'quantity': 0.0,
        'active': True,
        'read_only': False,
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
        #(_check_quantity, "Quantity can't be negative.", ['quantity']),
        (_check_duplicate, "Two cells can't share the same date.", ['date']),
        # Constraint below is not required as the matrix code will remove out of range cells
        #(_check_date, "Cell date is out of the activity report date range.", ['date']),
        ]

smile_activity_report_cell()
