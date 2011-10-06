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



class smile_project(osv.osv):
    _name = 'smile.project'

    _order = "start_date"

    _columns = {
        'name': fields.char('Name', size=32),
        'start_date': fields.date('Start', required=True),
        'end_date': fields.date('End', required=True),
        'line_ids': fields.one2many('smile.project.line', 'project_id', "Project lines"),
        'matrix_line_ids': fields.related('line_ids', type='one2many', relation='smile.project.line', string="Project lines", readonly=True),
        }

    _defaults = {
        'start_date': datetime.datetime.today().strftime('%Y-%m-%d'),
        'end_date': (datetime.datetime.today() + datetime.timedelta(days=7)).strftime('%Y-%m-%d'),
        }


    ## Constraints

    def _check_date_range(self, cr, uid, ids, context=None):
        for project in self.browse(cr, uid, ids, context):
            start_date = datetime.datetime.strptime(project.start_date, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(project.end_date, '%Y-%m-%d')
            if end_date < start_date:
                return False
        return True

    _constraints = [
        (_check_date_range, "Start date can't be greater than end date.", ['start_date', 'end_date'])
        ]


    ## Native methods

    def write(self, cr, uid, ids, vals, context=None):
        ret = super(smile_project, self).write(cr, uid, ids, vals, context)
        # Automaticcaly remove out of range cells if dates changes
        if 'start_date' in vals or 'end_date' in vals:
            self.remove_outdated_cells(cr, uid, ids, vals, context)
        return ret


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

    def matrix(self, cr, uid, ids, context=None):
        if len(ids) > 1:
            raise osv.except_osv('Error', 'len(ids) !=1')
        project = self.browse(cr, uid, ids[0], context)
        vals = {}
        # Set default values for all cells of the matrix
        for line in project.line_ids:
            # Populate our matrix with cell values found in the lines
            cell_value_holder = 'boolean_value'
            cell_type = 'boolean'
            if line.hold_quantities is True:
                cell_value_holder = 'quantity'
                cell_type = 'float'
            for cell in line.cell_ids:
                cell_date = datetime.datetime.strptime(cell.date, '%Y-%m-%d')
                vals['cell_%s_%s' % (line.id, cell_date.strftime('%Y%m%d'))] = (getattr(cell, cell_value_holder), cell_type)
            # Create empty cells for missing dates
            for date_str in self.pool.get('smile.matrix').get_date_range_as_str(project):
                cell_id = 'cell_%s_%s' % (line.id, date_str)
                if cell_id not in vals:
                    vals[cell_id] = (None, cell_type)
        new_context = context.copy()
        new_context['project_id'] = ids[0]
        matrix_id = self.pool.get('smile.matrix').create(cr, uid, vals, new_context)
        return {
            'name': "%s matrix" % (project.name,),
            'type': 'ir.actions.act_window',
            'res_model': 'smile.matrix',
            'res_id': matrix_id,
            'view_mode': 'form',
            'view_type': 'form',
            'context': new_context,
            'target': 'new',
            #'target': 'current',
            }

smile_project()



class smile_project_line(osv.osv):
    _name = 'smile.project.line'

    _columns = {
        'name': fields.char('Name', size=32, required=True),
        'project_id': fields.many2one('smile.project', "Project", required=True, ondelete='cascade'),
        'cell_ids': fields.one2many('smile.project.line.cell', 'line_id', "Cells"),
        # This property define if the line hold float quantities or booleans
        # This can be changed later to a line_type
        'hold_quantities': fields.boolean('Hold quantities'),
        }

    _defaults = {
        'hold_quantities': True,
        }


    ## Native methods

    def create(self, cr, uid, vals, context=None):
        line_id = super(smile_project_line, self).create(cr, uid, vals, context)
        # Create default cells
        line = self.browse(cr, uid, line_id, context)
        self.generate_cells(cr, uid, line, context)
        return line_id


    ## Custom methods

    def generate_cells(self, cr, uid, line, context=None):
        """ This method generate all cells between the date range.
        """
        date_range = self.pool.get('smile.project').get_date_range(line.project_id)
        vals = {
            'line_id': line.id
            }
        for date in date_range:
            vals.update({'date': date})
            self.pool.get('smile.project.line.cell').create(cr, uid, vals, context)
        return


smile_project_line()



class smile_project_line_cell(osv.osv):
    _name = 'smile.project.line.cell'

    _order = "date"


    ## Function fields

    def _get_cell_value_string(self, cr, uid, ids, name, arg, context=None):
        result = {}
        for cell in self.browse(cr, uid, ids, context):
            val = ''
            if cell.hold_quantities:
                val = cell.quantity
            else:
                val = cell.boolean_value
            result[cell.id] = str(val)
        return result


    ## Fields definition

    _columns = {
        'date': fields.date('Date', required=True),
        'quantity': fields.float('Quantity', required=True),
        'boolean_value': fields.boolean('Boolean Value', required=True),
        'line_id': fields.many2one('smile.project.line', "Project line", required=True, ondelete='cascade'),
        'hold_quantities': fields.related('line_id', 'hold_quantities', type='boolean', string="Hold quantities", readonly=True),
        'cell_value_string': fields.function(_get_cell_value_string, string="Cell value", type='string', readonly=True, method=True),
        }

    _defaults = {
        'quantity': 0.0,
        'boolean_value': False,
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
            project = cell.line_id.project_id
            start_date = datetime.datetime.strptime(project.start_date, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(project.end_date, '%Y-%m-%d')
            if date < start_date or date > end_date:
                return False
        return True

    def _check_duplicate(self, cr, uid, ids, context=None):
        for cell in self.browse(cr, uid, ids, context):
            if len(self.search(cr, uid, [('date', '=', cell.date), ('line_id', '=', cell.line_id.id)], context=context)) > 1 :
                return False
        return True

    _constraints = [
        (_check_quantity, "Quantity can't be negative.", ['quantity']),
        (_check_date, "Cell date is out of the project date range.", ['date']),
        (_check_duplicate, "Two cells can't share the same date.", ['date']),
        ]

smile_project_line_cell()
