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
            # Get the list of all objects new rows of the matrix can be linked to
            p = parent_obj.pool.get('smile.activity.project')
            new_row_list = [(o.id, o.name) for o in p.browse(cr, uid, p.search(cr, uid, [], context=context), context) if o.value_type == 'float']
            # Get the list of all dates (active and inactive) composing the period
            date_range = [self.date_to_str(d) for d in parent_obj.pool.get('smile.activity.period').get_date_range(parent_obj.period_id)]
            # Browse all lines that will compose our matrix
            lines = getattr(parent_obj, line_ids_property_name, [])
            for line in lines:
                line_data = {}
                # Get all cells of the line
                line_data.update({
                    'id': line.id,
                    'name': line.name,
                    'type': line.line_type,
                    })
                cells = getattr(line, cell_ids_property_name, [])
                cells_data = {}
                for cell in cells:
                    cell_date = datetime.datetime.strptime(cell.date, '%Y-%m-%d')
                    cells_data[cell_date.strftime('%Y%m%d')] = cell.cell_value
                line_data.update({'cells_data': cells_data})
                matrix_data.append(line_data)
            # Add a row template at the end
            matrix_data.append({
                'id': "template",
                'name': "Row template",
                'type': "float",
                'cells_data': dict([(datetime.datetime.strptime(l.date, '%Y-%m-%d').strftime('%Y%m%d'), 0.0) for l in parent_obj.period_id.active_line_ids]),
                })
            # Pack all data required to render the matrix
            matrix_list.update({
                parent_obj.id: {
                    'matrix_data': matrix_data,
                    'date_range': date_range,
                    'new_row_list': new_row_list,
                    }
                })
        return matrix_list



class smile_activity_report(osv.osv):
    _name = 'smile.activity.report'

    #_order = "start_date"

    _columns = {
        'name': fields.char('Name', size=32),
        'period_id': fields.many2one('smile.activity.period', "Period", required=True),
        'start_date': fields.related('period_id', 'start_date', type='date', string="Start date", readonly=True),
        'end_date': fields.related('period_id', 'end_date', type='date', string="End date", readonly=True),
        'line_ids': fields.one2many('smile.activity.report.line', 'report_id', "Activity lines"),
        'matrix_line_ids': matrix('line_ids', 'cell_ids', string="Activity report lines", readonly=False),
        }


    ## Native methods

    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        result = super(smile_activity_report, self).read(cr, uid, ids, fields, context, load)
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
                    if not (f_id_elements[1].startswith('new') or f_id_elements[1].startswith('template')):
                        line_id = int(f_id_elements[1])
                        cell_date = datetime.datetime.strptime(f_id_elements[2], '%Y%m%d')
                        cell_id = self.pool.get('smile.activity.report.cell').search(cr, uid, [('date', '=', cell_date), ('line_id', '=', line_id)], limit=1, context=context)
                        if cell_id:
                            cell = self.pool.get('smile.activity.report.cell').browse(cr, uid, cell_id, context)[0]
                            cell_value = cell.cell_value
                    props.update({f_id: cell_value})
            updated_result.append(props)
        if isinstance(ids, (int, long)):
            updated_result = updated_result[0]
        return updated_result

    def write(self, cr, uid, ids, vals, context=None):
        ret = super(smile_activity_report, self).write(cr, uid, ids, vals, context)
        # Automaticcaly remove out of range cells if dates changes
        if 'start_date' in vals or 'end_date' in vals:
            self.update_cells(cr, uid, ids, context)
        written_lines = []
        for report in self.browse(cr, uid, ids, context):
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
                    line_project_id = int(line_id[3:])
                    line_id = None
                    if line_project_id in new_lines:
                        line_id = new_lines[line_project_id]
                    else:
                        vals = {
                            'report_id': report.id,
                            'project_id': line_project_id,
                            }
                        line_id = self.pool.get('smile.activity.report.line').create(cr, uid, vals, context)
                        new_lines[line_project_id] = line_id
                else:
                    line_id = int(line_id)
                written_lines.append(line_id)
                # Get the line
                line = self.pool.get('smile.activity.report.line').browse(cr, uid, line_id, context)
                # Convert the raw value to the right one depending on the type of the line
                if line.line_type != 'boolean':
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
                cell_vals = {
                    'quantity': cell_value,
                    }
                # Search for an existing cell at the given date
                cell = self.pool.get('smile.activity.report.cell').search(cr, uid, [('date', '=', cell_date), ('line_id', '=', line_id)], context=context, limit=1)
                # Cell doesn't exists, create it
                if not cell:
                    cell_vals.update({
                        'date': cell_date,
                        'line_id': line_id,
                        })
                    self.pool.get('smile.activity.report.cell').create(cr, uid, cell_vals, context)
                # Update cell with our data
                else:
                    cell_id = cell[0]
                    self.pool.get('smile.activity.report.cell').write(cr, uid, cell_id, cell_vals, context)
        # If there was no references to one of our line it means it was deleted
        for report in self.browse(cr, uid, ids, context):
            removed_lines = list(set([l.id for l in report.line_ids]).difference(set(written_lines)))
            self.pool.get('smile.activity.report.line').unlink(cr, uid, removed_lines, context)
        return ret


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
