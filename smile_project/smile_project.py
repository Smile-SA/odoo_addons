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



class matrix(fields.dummy):
    """ A custom field to prepare data for, and mangle data from, the matrix widget
    """

    def date_to_str(self, date):
        return date.strftime('%Y%m%d')


    def _fnct_read(self, obj, cr, uid, ids, field_name, args, context=None):
        """ Dive into object lines and cells, and organize their info to let the matrix widget understand them
        """
        line_ids_property_name = args[0]
        cell_ids_property_name = args[1]
        matrix_list = {}
        obj_list = obj.browse(cr, uid, ids, context)
        for parent_obj in obj_list:
            matrix_data = []
            date_range = [self.date_to_str(d) for d in parent_obj.pool.get('smile.project').get_date_range(parent_obj)]
            lines = getattr(parent_obj, line_ids_property_name, [])
            for line in lines:
                line_data = {}
                # Populate our matrix with cell values found in the lines
                cell_value_holder = 'boolean_value'
                cell_type = 'boolean'
                if line.hold_quantities is True:
                    cell_value_holder = 'quantity'
                    cell_type = 'float'
                line_data.update({
                    'id': line.id,
                    'name': line.name,
                    'type': cell_type,
                    })
                cells = getattr(line, cell_ids_property_name, [])
                cells_data = {}
                for cell in cells:
                    cell_date = datetime.datetime.strptime(cell.date, '%Y-%m-%d')
                    cells_data[cell_date.strftime('%Y%m%d')] = getattr(cell, cell_value_holder)
                line_data.update({'cells_data': cells_data})
                matrix_data.append(line_data)
            matrix_list.update({
                parent_obj.id: {
                    'matrix_data': matrix_data,
                    'date_range': date_range,
                    }
                })
        return matrix_list



class smile_project(osv.osv):
    _name = 'smile.project'

    #_order = "start_date"

    _columns = {
        'name': fields.char('Name', size=32),
        'period_id': fields.many2one('smile.period', "Period", required=True),
        'start_date': fields.related('period_id', 'start_date', type='date', string="Start date", readonly=True),
        'end_date': fields.related('period_id', 'end_date', type='date', string="End date", readonly=True),
        'line_ids': fields.one2many('smile.project.line', 'project_id', "Project lines"),
        'matrix_line_ids': matrix('line_ids', 'cell_ids', string="Project lines", readonly=False),
        }


    ## Native methods

    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        result = super(smile_project, self).read(cr, uid, ids, fields, context, load)
        # Let anyone read a cell value directly using the cell_LineID_YYYYMMMDD scheme
        if isinstance(ids, (int, long)):
            result = [result]
        updated_result = []
        for props in result:
            unread_fields = set(fields).difference(set(props.keys()))
            for f_id in unread_fields:
                f_id_elements = f_id.split('_')
                if len(f_id_elements) == 3 and f_id_elements[0] == 'cell':
                    cell_value = None
                    if not f_id_elements[1].startswith('new'):
                        line_id = int(f_id_elements[1])
                        cell_date = datetime.datetime.strptime(f_id_elements[2], '%Y%m%d')
                        #project = self.browse(cr, uid, props['id'], context)
                        cell_id = self.pool.get('smile.project.line.cell').search(cr, uid, [('date', '=', cell_date), ('line_id', '=', line_id)], limit=1, context=context)
                        if cell_id:
                            cell = self.pool.get('smile.project.line.cell').browse(cr, uid, cell_id, context)[0]
                            if cell.hold_quantities:
                                cell_value = cell.quantity
                            else:
                                cell_value = cell.boolean_value
                    props.update({f_id: cell_value})
            updated_result.append(props)
        if isinstance(ids, (int, long)):
            updated_result = updated_result[0]
        return updated_result

    def write(self, cr, uid, ids, vals, context=None):
        ret = super(smile_project, self).write(cr, uid, ids, vals, context)
        # Automaticcaly remove out of range cells if dates changes
        if 'start_date' in vals or 'end_date' in vals:
            self.remove_outdated_cells(cr, uid, ids, vals, context)
        written_lines = []
        for project in self.browse(cr, uid, ids, context):
            new_lines = {}
            # Parse and clean-up data coming from the matrix
            for (cell_name, cell_value) in vals.items():
                # Filters out non cell values and template row
                if not cell_name.startswith('cell_') or cell_name.startswith('cell_template'):
                    continue
                cell_name_fragments = cell_name.split('_')
                cell_date = datetime.datetime.strptime(cell_name_fragments[2], '%Y%m%d')
                # Are we updating an existing line or creating a new one ?
                line_id = cell_name_fragments[1]
                if line_id.startswith('new'):
                    line_name = line_id
                    line_id = None
                    if line_name in new_lines:
                        line_id = new_lines[line_name]
                    else:
                        vals = {
                            'project_id': project.id,
                            'name': line_name,
                            }
                        line_id = self.pool.get('smile.project.line').create(cr, uid, vals, context)
                        new_lines[line_name] = line_id
                else:
                    line_id = int(line_id)
                written_lines.append(line_id)
                # Get the line
                line = self.pool.get('smile.project.line').browse(cr, uid, line_id, context)
                # Convert the raw value to the right one depending on the type of the line
                if line.hold_quantities:
                    # Quantity conversion
                    if type(cell_value) is type(''):
                        cell_value = float(cell_value)
                    else:
                        cell_value = None
                else:
                    # Boolean conversion
                    if cell_value == '1':
                        cell_value = True
                    else:
                        cell_value = False
                # Ignore non-modified cells
                if cell_value is None:
                    continue
                # Prepare the cell value
                cell_vals = {}
                if line.hold_quantities:
                    cell_vals.update({'quantity': cell_value})
                else:
                    cell_vals.update({'boolean_value': cell_value})
                # Search for an existing cell at the given date
                cell = self.pool.get('smile.project.line.cell').search(cr, uid, [('date', '=', cell_date), ('line_id', '=', line_id)], context=context, limit=1)
                # Cell doesn't exists, create it
                if not cell:
                    cell_vals.update({
                        'date': cell_date,
                        'line_id': line_id,
                        })
                    self.pool.get('smile.project.line.cell').create(cr, uid, cell_vals, context)
                # Update cell with our data
                else:
                    cell_id = cell[0]
                    self.pool.get('smile.project.line.cell').write(cr, uid, cell_id, cell_vals, context)
        # If there was no references to one of our line it means it was deleted
        for project in self.browse(cr, uid, ids, context):
            removed_lines = list(set([l.id for l in project.line_ids]).difference(set(written_lines)))
            self.pool.get('smile.project.line').unlink(cr, uid, removed_lines, context)
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
