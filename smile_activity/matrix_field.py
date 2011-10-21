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
        return datetime.date.strftime('%Y%m%d')

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
            new_row_list = [(o.id, o.name) for o in p.browse(cr, uid, p.search(cr, uid, [('value_type', '=', 'float'), ('required', '=', False)], context=context), context)]
            # Get the list of all dates (active and inactive) composing the period
            date_range = [self.date_to_str(d) for d in parent_obj.pool.get('smile.activity.period').get_date_range(parent_obj.period_id)]
            # Browse all lines that will compose our matrix
            lines = getattr(parent_obj, line_ids_property_name, [])
            for line in lines:
                # Transfer some line data to the matrix widget
                line_data = {
                    'id': line.id,
                    'name': line.name,
                    'type': line.line_type,
                    'required': line.project_id.required,
                    }
                # Get all cells of the line
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
