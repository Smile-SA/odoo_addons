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
            new_row_list = [(o.id, o.name) for o in p.browse(cr, uid, p.search(cr, uid, [('value_type', '=', 'float')], context=context), context)]
            # Get the list of all dates (active and inactive) composing the period
            date_range = [self.date_to_str(d) for d in parent_obj.pool.get('smile.activity.period').get_date_range(parent_obj.period_id)]
            # Browse all lines that will compose our matrix
            lines = getattr(parent_obj, line_ids_property_name, [])
            for line in lines:
                # Transfer some line data to the matrix widget
                line_data = {
                    'id': line.id,
                    'uid': line.project_id.id,
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
                'uid': "template",
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
                    'column_date_label_format': '%d',
                    }
                })
        return matrix_list



class multiline_matrix(fields.dummy):
    """ A custom field to prepare data for, and mangle data from, the matrix widget.
        TODO: merge this field definition with the one above and let all matrix options be passed as parameter for high configurability
    """

    def date_to_str(self, date):
        return date.strftime('%Y%m%d')

    def _fnct_read(self, obj, cr, uid, ids, field_name, args, context=None):
        """ Dive into object lines and cells, and organize their info to let the matrix widget understand them
        """
        # Get the matrix parameters
        # XXX Haven't found a cleaner way to get my matrix parameters... Any help is welcome ! :)
        # Property name from which we get the lines composing the matrix
        line_source = self.__dict__.get('line_source', None)
        # Property name from which we get the cells composing the matrix.
        # Cells are fetched from the lines as defined above.
        cell_source = self.__dict__.get('cell_source', None)
        # Property name of the relation field on which we'll call a get_date_range() method
        date_range_source = self.__dict__.get('date_range_source', None)
        # The format we use to display date labels
        date_format = self.__dict__.get('date_format', None)
        # The object type we use to create new rows
        new_row_source_type = self.__dict__.get('new_row_source_type', None)
        # Check that all required parameters are there
        for p_name in ['line_source', 'cell_source', 'date_range_source']:
            if not p_name:
                raise osv.except_osv('Error !', "%s parameter is missing." % p_name)

        # Browse through all objects on which our matrix field is defined
        matrix_list = {}
        for base_object in obj.browse(cr, uid, ids, context):
            matrix_data = []

            # Get the list of all objects new rows of the matrix can be linked to
            new_row_list = []
            if new_row_source_type:
                p = base_object.pool.get(new_row_source_type)
                new_row_list = [(o.id, o.name) for o in p.browse(cr, uid, p.search(cr, uid, [], context=context), context)]

            # Get the date range composing the timeline
            date_range_source_object = getattr(base_object, date_range_source, None)
            if not date_range_source_object:
                raise osv.except_osv('Error !', "%r has no %s property." % (base_object, date_range_source))
            date_range = getattr(date_range_source_object, 'date_range', None)
            if date_range is None:
                raise osv.except_osv('Error !', "%r has no date_range property." % date_range_source_object)
            if type(date_range) is not type([]):
                raise osv.except_osv('Error !', "date_range must return data that looks like selection field data.")
            # Format our date range for our matrix
            date_range = [self.date_to_str(d) for (d, l) in date_range]

            ## Browse all lines that will compose our matrix
            #lines = getattr(base_object, line_source, [])
            #for line in lines:
                ## Transfer some line data to the matrix widget
                #line_data = {
                    #'id': line.id,
                    #'name': line.name,
                    #'type': line.line_type,
                    #'required': line.project_id.required,
                    #}
                ## Get all cells of the line
                #cells = getattr(line, cell_source, [])
                #cells_data = {}
                #for cell in cells:
                    #cell_date = datetime.datetime.strptime(cell.date, '%Y-%m-%d')
                    #cells_data[cell_date.strftime('%Y%m%d')] = cell.cell_value
                #line_data.update({'cells_data': cells_data})
                #matrix_data.append(line_data)

            # Add a row template at the end
            matrix_data.append({
                'id': "template",
                'uid': "template",
                'name': "Row template",
                'type': "float",
                'cells_data': {},
                })

            # Pack all data required to render the matrix
            matrix_list.update({
                base_object.id: {
                    'matrix_data': matrix_data,
                    'date_range': date_range,
                    'new_row_list': new_row_list,
                    'column_date_label_format': date_format,
                    'class': 'multiline',
                    }
                })
        return matrix_list
