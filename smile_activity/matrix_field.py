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
    """ A custom field to prepare data for, and mangle data from, the matrix widget.
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
        # Property name of the relation field on which we'll call the date_range property
        date_range_source = self.__dict__.get('date_range_source', None)
        # The format we use to display date labels
        date_format = self.__dict__.get('date_format', None)
        # The object type we use to create new rows
        resource_type = self.__dict__.get('resource_type', None)
        # Get the property of line from which we derive the matrix resource
        line_resource_source = self.__dict__.get('line_resource_source', None)
        # Additional classes can be manually added
        css_class = self.__dict__.get('css_class', [])

        # Check that all required parameters are there
        for p_name in ['line_source', 'cell_source', 'date_range_source']:
            if not p_name:
                raise osv.except_osv('Error !', "%s parameter is missing." % p_name)

        # Browse through all objects on which our matrix field is defined
        matrix_list = {}
        for base_object in obj.browse(cr, uid, ids, context):
            matrix_data = []

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

            # Get the list of all objects new rows of the matrix can be linked to
            resource_list = []
            if resource_type:
                p = base_object.pool.get(resource_type)
                resource_list = [(o.id, o.name) for o in p.browse(cr, uid, p.search(cr, uid, [], context=context), context)]

            # Browse all lines that will compose our matrix
            lines = getattr(base_object, line_source, [])
            for line in lines:
                # Transfer some line data to the matrix widget
                line_data = {
                    'id': line.id,
                    'name': line.name,
                    'type': line.line_type,
                    'required': line.project_id.required,
                    }

                # Get the row UID corresponding to the line
                if line_resource_source is not None:
                    line_ressource = getattr(line, line_resource_source, None)
                    if line_ressource is None:
                        raise osv.except_osv('Error !', "%r has no %s property." % (line, line_ressource))
                    line_data.update({'res_id': line_ressource.id})

                # Get all cells of the line
                cells = getattr(line, cell_source, [])
                cells_data = {}
                for cell in cells:
                    cell_date = datetime.datetime.strptime(cell.date, '%Y-%m-%d')
                    cells_data[cell_date.strftime('%Y%m%d')] = cell.cell_value
                line_data.update({'cells_data': cells_data})
                matrix_data.append(line_data)

            # Get the list of active dates that will serve us to populate default content of the row template cells.
            # TODO: Make a little bit more clear by defining a "default_cell_value" method of some sort
            active_dates = {}
            active_date_range = getattr(date_range_source_object, 'active_date_range', None)
            if active_date_range is not None:
                if type(active_date_range) is not type([]):
                    raise osv.except_osv('Error !', "active_date_range must return data that looks like selection field data.")
                active_dates = dict([(datetime.datetime.strptime(d, '%Y-%m-%d').strftime('%Y%m%d'), 0.0) for (d, l) in active_date_range])

            # Add a row template at the end
            matrix_data.append({
                'id': "template",
                'res_id': "template",
                'name': "Row template",
                'type': "float",
                'cells_data': active_dates,
                })

            # Pack all data required to render the matrix
            matrix_def = {
                'matrix_data': matrix_data,
                'date_range': date_range,
                'resource_list': resource_list,
                'column_date_label_format': date_format,
                'class': css_class
                }

            if self.__dict__.get('experimental_slider', False):
                matrix_def['class'] = matrix_def['class'] + ['slider']

            matrix_list.update({base_object.id: matrix_def})
        return matrix_list



def matrix_read_patch(func):
    """
    Let the matrix read the temporary fields that are not persistent in database.
    Raise an exception if it tries to read a field that doesn't follow Matrix widget conventions.
    Valid matrix field names:
        * resource_list  (ignored)
        * res_template  (ignored)
        * res_XX
        * cell_XX_YYYYMMDD
        * cell_template_YYYYMMDD  (ignored)
    """
    def read_matrix_virtual_fields(*arg, **kw):
        result = func(*arg, **kw)
        obj = arg[0]
        cr = arg[1]
        uid = arg[2]
        ids = arg[3]
        fields = arg[4]
        context = kw.get('context', None)
        if isinstance(ids, (int, long)):
            result = [result]
        updated_result = []
        cell_pool = obj.pool.get('smile.activity.report.cell')
        for props in result:
            unread_fields = set(fields).difference(set(props.keys()))
            for f_id in unread_fields:
                f_id_elements = f_id.split('_')
                # Ignore valid but unneccesary fields
                if f_id in ['resource_list', 'res_template'] or f_id.startswith('cell_template_'):
                    continue
                # Handle cell_XX_YYYYMMDD fields
                elif f_id_elements[0] == 'cell' and len(f_id_elements) == 3:
                    cell_value = None
                    if not f_id_elements[1].startswith('new'):
                        line_id = int(f_id_elements[1])
                        cell_date = datetime.datetime.strptime(f_id_elements[2], '%Y%m%d')
                        cell_id = cell_pool.search(cr, uid, [('date', '=', cell_date), ('line_id', '=', line_id)], limit=1, context=context)
                        if cell_id:
                            cell = cell_pool.browse(cr, uid, cell_id, context)[0]
                            cell_value = cell.cell_value
                    props.update({f_id: cell_value})
                # Handle res_XX fields
                elif f_id_elements[0] == 'res' and len(f_id_elements) == 2:
                    #TODO
                    pass
                # Requested field doesn't follow matrix convention
                else:
                    import pdb; pdb.set_trace()
                    raise osv.except_osv('Error !', "Field %s doesn't respect matrix widget conventions." % f_id)
            updated_result.append(props)
        if isinstance(ids, (int, long)):
            updated_result = updated_result[0]
        return updated_result
    return read_matrix_virtual_fields
