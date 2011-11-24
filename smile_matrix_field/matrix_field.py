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



def _get_prop(obj, prop_name, default_value=None):
    """ Get a property value
    """
    if not prop_name:
        return default_value
    prop_value = getattr(obj, prop_name, default_value)
    if prop_value is None:
        raise osv.except_osv('Error !', "%r has no %s property." % (obj, prop_name))
    return prop_value


def _get_date_range(base_object, date_range_property, active_date_range_property):
    """ Utility method to get the displayed date range and the active date range.
        This piece of code was moved in its own method as date range extraction requires some special handling.
    """
    # Get on the current object the date range bounding the timeline
    date_range = _get_prop(base_object, date_range_property)
    # Get the active date range. Default is to let all dates of the displayed range.
    active_date_range = _get_prop(base_object, active_date_range_property, date_range)

    # date_range and active_date_range values may be stored as text (or selection, which is the same). In this case, we need to evaluate them. It's bad, but it works.
    if isinstance(date_range, (str, unicode)):
        date_range = eval(date_range)
    if isinstance(active_date_range, (str, unicode)):
        active_date_range = eval(active_date_range)
        if not active_date_range:
            active_date_range = date_range

    # Check the data structure returned by date ranges
    for (range_name, range_data) in [(date_range_property, date_range), (active_date_range_property, active_date_range)]:
        if type(range_data) is not type([]):
            raise osv.except_osv('Error !', "%s must return data that looks like selection field data." % range_name)
        for d in range_data:
            if not isinstance(d, datetime.date):
                raise osv.except_osv('Error !', "%s must return a list of dates." % range_name)

    return (date_range, active_date_range)


class matrix(fields.dummy):
    """ A custom field to prepare data for, and mangle data from, the matrix widget.
    """

    ## Utility methods

    def _date_to_str(self, date):
        return date.strftime('%Y%m%d')

    def _str_to_date(self, date):
        """ Transform string date to a proper date object
        """
        if not isinstance(date, datetime.date):
            date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        return date

    def _get_title_or_id(self, obj):
        """ Return the title of the object or a descriptive string
        """
        return getattr(obj, 'name', None) or getattr(obj, 'title', None) or 'Untitled (ID: %s)' % obj.id


    ## Native methods

    def _fnct_read(self, obj, cr, uid, ids, field_name, args, context=None):
        """ Dive into object lines and cells, and organize their info to let the matrix widget understand them
        """
        # Get the matrix parameters
        # TODO: guess line_type, cell_type and resource_type based on their xxx_property parameter counterparts
        # XXX Haven't found a cleaner way to get my matrix parameters... Any help is welcome ! :)
        # Property name from which we get the lines composing the matrix
        line_property = self.__dict__.get('line_property', None)
        line_type = self.__dict__.get('line_type', None)
        line_inverse_property = self.__dict__.get('line_inverse_property', None)
        # Get line properties from which we derive the matrix resources
        line_resource_property_list = self.__dict__.get('line_resource_property_list', None)
        default_widget_type = self.__dict__.get('default_widget_type', 'float')
        dynamic_widget_type_property = self.__dict__.get('dynamic_widget_type_property', None)
        # Property name from which we get the cells composing the matrix.
        # Cells are fetched from the lines as defined above.
        cell_property = self.__dict__.get('cell_property', None)
        cell_type = self.__dict__.get('cell_type', None)
        cell_inverse_property = self.__dict__.get('cell_inverse_property', None)
        cell_value_property = self.__dict__.get('cell_value_property', None)
        cell_date_property = self.__dict__.get('cell_date_property', None)
        default_cell_value = self.__dict__.get('default_cell_value', 0.0)
        # Property name of the relation field on which we'll call the date_range property
        date_range_property = self.__dict__.get('date_range_property', None)
        active_date_range_property = self.__dict__.get('active_date_range_property', None)
        # The format we use to display date labels
        date_format = self.__dict__.get('date_format', "%Y-%m-%d")
        # We can add read-only columns at the end of the matrix
        additional_sum_columns = self.__dict__.get('additional_sum_columns', [])
        # Same as above, but for lines
        additional_line_property =  self.__dict__.get('additional_line_property', None)
        # Additional classes can be manually added
        css_classes = self.__dict__.get('css_classes', [])
        # Get the matrix title
        title = self.__dict__.get('title', "Lines")

        # Check that all required parameters are there
        for p_name in ['line_property', 'line_type', 'line_inverse_property', 'line_resource_property_list', 'cell_property', 'cell_type', 'cell_inverse_property', 'cell_value_property', 'cell_date_property']:
            if not p_name:
                raise osv.except_osv('Error !', "%s parameter is missing." % p_name)

        # line_resource_property_list required at least one parameter
        if type(line_resource_property_list) != type([]) or len(line_resource_property_list) < 1:
            raise osv.except_osv('Error !', "line_resource_property_list parameter must be a list with at least one element.")

        # Browse through all objects on which our matrix field is defined
        matrix_list = {}
        for base_object in obj.browse(cr, uid, ids, context):
            matrix_data = []

            # Get our date ranges
            (date_range, active_date_range) = _get_date_range(base_object, date_range_property, active_date_range_property)

            # Get the list of all objects new rows of the matrix can be linked to
            # Keep the original order defined in matrix properties
            resource_value_list = []
            for (res_id, res_type) in line_resource_property_list:
                p = base_object.pool.get(res_type)
                resource_value_list.append({
                    'id': res_id,
                    'values': [(o.id, self._get_title_or_id(o)) for o in p.browse(cr, uid, p.search(cr, uid, [], context=context), context)],
                    })

            # Browse all lines that will compose our the main part of the matrix
            lines = [(line, 'body') for line in _get_prop(base_object, line_property, [])]
            # Add bottom lines if provided
            if additional_line_property:
                lines += [(line, 'bottom') for line in _get_prop(base_object, additional_line_property, [])]
            for (line, line_position) in lines:
                # Transfer some line data to the matrix widget
                line_data = {
                    'id': line.id,
                    'name': self._get_title_or_id(line),
                    # Is this resource required ?
                    # FIX: 'required': getattr(getattr(line, line_resource_property), 'required', False),
                    }

                # Get the type of the widget we'll use to display cell values
                line_widget = _get_prop(line, dynamic_widget_type_property, default_widget_type)
                # In case if boolean widget, force the position to bottom
                if line_widget == 'boolean':
                    line_position = 'bottom'
                # Force bottom line to be non-editable
                line_read_only = False
                if line_position == 'bottom':
                    line_read_only = True
                line_data.update({
                    'widget': line_widget,
                    'position': line_position,
                    'read_only': line_read_only,
                    })

                # Get all resources of the line
                # Keep the order defined by matrix field's properties
                res_list = []
                for (res_id, res_type) in line_resource_property_list:
                    res = _get_prop(line, res_id)
                    res_list.append({
                        'id': res_id,
                        'label': self._get_title_or_id(res),
                        'value': res.id,
                        })
                line_data.update({'resources': res_list})

                # Get all cells of the line, indexed by their IDs
                cells = dict([(cell.id, cell) for cell in _get_prop(line, cell_property, [])])
                # Provide to the matrix a cell for each active date in the range
                cells_data = {}
                for d in active_date_range:
                    # Find a cell corresponding to the date in the date_range
                    cell_value = default_cell_value
                    for (cell_id, cell) in cells.items():
                        cell_date = datetime.datetime.strptime(_get_prop(cell, cell_date_property), '%Y-%m-%d').date()
                        if cell_date == d:
                            cells.pop(cell_id)
                            cell_value = _get_prop(cell, cell_value_property, default_cell_value)
                            break
                    cells_data[d.strftime('%Y%m%d')] = cell_value
                line_data.update({'cells_data': cells_data})
                # Remove all out of date and duplicate cells
                obj.pool.get(cell_type).unlink(cr, uid, cells.keys(), context)

                # Get data of additional columns
                for line_property in [c['line_property'] for c in additional_sum_columns if 'line_property' in c]:
                    if line_property in line_data:
                        raise osv.except_osv('Error !', "line property %s conflicts with matrix line definition." % line_property)
                    v = _get_prop(line, line_property)
                    if type(v) != type(0.0):
                        v = float(v)
                    line_data.update({line_property: v})

                matrix_data.append(line_data)

            # Get default cells and their values for the template row.
            template_cells_data = {}
            template_cells_data = dict([(self._date_to_str(d), default_cell_value) for d in active_date_range])
            template_resources = [{
                    'id': res_id,
                    'label': res_id.replace('_', ' ').title(),
                    'value': 0,
                    } for (res_id, res_type) in line_resource_property_list]
            # Add a row template at the end
            matrix_data.append({
                'id': "template",
                'name': "Row template",
                'widget': default_widget_type,
                'cells_data': template_cells_data,
                'resources': template_resources,
                })

            # Pack all data required to render the matrix
            matrix_def = {
                'matrix_data': matrix_data,
                'date_range': [self._date_to_str(d) for d in date_range],  # Format our date range for our matrix # XXX Keep them as date objects ?
                'resource_value_list': resource_value_list,
                'column_date_label_format': date_format,
                'additional_columns': additional_sum_columns,
                'class': css_classes,
                'title': title,
                }

            if self.__dict__.get('experimental_slider', False):
                matrix_def['class'] = matrix_def['class'] + ['slider']

            matrix_list.update({base_object.id: matrix_def})
        return matrix_list



def get_matrix_conf(osv_instance, matrix_id=None):
    """ Utility method to get the configuration of the matrix field defined on the class the provided object is an instance of.
        XXX only one matrix field is allowed per object class.
    """
    field_defs = osv_instance.__dict__['_columns']
    matrix_fields = dict([(f_id, f.__dict__) for (f_id, f) in field_defs.items() if f.__dict__.get('_fnct', None) and getattr(f.__dict__['_fnct'], 'im_class', None) and f.__dict__['_fnct'].im_class.__module__ == globals()['__name__']])
    if not len(matrix_fields):
        return None
    if matrix_id:
        return matrix_fields.get(matrix_id, None)
    return matrix_fields



def parse_virtual_field_id(id_string):
    """ This utility method parse and validate virtual fields coming from the matrix
        Raise an exception if it tries to read a field that doesn't follow Matrix widget conventions.
        Return None for fields generated by the matrix but not usefull for data input.
        Valid matrix field names:
            * MATRIX_ID_res_XX_PROPERTY_ID
            * MATRIX_ID_res_newXX_PROPERTY_ID
            * MATRIX_ID_res_template_PROPERTY_ID  (ignored)
            * MATRIX_ID_res_dummyXX_PROPERTY_ID   (ignored)
            * MATRIX_ID_res_list_PROPERTY_ID      (ignored)
            * MATRIX_ID_cell_XX_YYYYMMDD
            * MATRIX_ID_cell_newXX_YYYYMMDD
            * MATRIX_ID_cell_template_YYYYMMDD    (ignored)
        XXX Can we increase the readability of the validation rules embedded in this method by using reg exps ?
    """
    # Separate the matrix ID and the field ID
    matrix_id = None
    RESERVED_IDS = ['cell', 'res']
    for reserved_id in RESERVED_IDS:
        splits = id_string.split('_%s_' % reserved_id)
        if len(splits) < 2:
            continue
        # Two instances of a reserved ID was found,
        # or we already found a matrix ID but we can still split with another reserved ID.
        # In either case, that's bad !
        if len(splits) > 2 or matrix_id is not None:
            raise osv.except_osv('Error !', "Field %r is composed of two reserved IDs %r." % (id_string, RESERVED_IDS))
        matrix_id = splits[0]
    if not matrix_id:
        raise osv.except_osv('Error !', "Field %r has no matrix ID as a prefix." % id_string)
    f_id = id_string[len(matrix_id)+1:]
    f_id_elements = f_id.split('_')

    # Check fields element lenght depending on their type
    if (f_id_elements[0] == 'cell' and len(f_id_elements) == 3) or \
       (f_id_elements[0] == 'res'  and len(f_id_elements) > 2):

        # Silently ignore some fields that are used for interactivity only by the matrix javascript
        if f_id.startswith('cell_template_') or \
           f_id.startswith('res_template_')  or \
           f_id.startswith('res_dummy')      or \
           f_id.startswith('res_list_'):
            return None

        # For ressource, the last parameter is the property ID of the line the resource belong to. Recompose it
        if f_id_elements[0] == 'res':
            f_id_elements = f_id_elements[:2] + ['_'.join(f_id_elements[2:])]
            # TODO: check that the PROPERTY_ID (aka f_id_elements[2]) exist as a column in the line data model

        # Check that the date is valid
        if f_id_elements[0] == 'cell':
            date_element = f_id_elements[2]
            try:
                datetime.datetime.strptime(date_element, '%Y%m%d').date()
            except ValueError:
                raise osv.except_osv('Error !', "Field %r don't have a valid %r date element." % (id_string, date_element))

        # Check that that the second element is an integer. It is allowed to starts with the 'new' prefix.
        id_element = f_id_elements[1]
        if id_element.startswith('new'):
            id_element = id_element[3:]
        if str(int(id_element)) == id_element:
            return [matrix_id] + f_id_elements

    # Requested field doesn't follow matrix convention
    raise osv.except_osv('Error !', "Field %r doesn't respect matrix widget conventions." % id_string)



def matrix_read_patch(func):
    """
    Let the matrix read the temporary fields that are not persistent in database.
    """
    def read_matrix_virtual_fields(*arg, **kw):
        result = func(*arg, **kw)
        (obj, cr, uid, ids, fields) = arg[:5]
        context = kw.get('context', None)
        if isinstance(ids, (int, long)):
            result = [result]
        updated_result = []
        for props in result:
            unread_fields = set(fields).difference(set(props.keys()))
            for (matrix_id, conf) in get_matrix_conf(obj).items():
                cell_pool = obj.pool.get(conf['cell_type'])
                line_pool = obj.pool.get(conf['line_type'])
                for f_id in unread_fields:
                    parsed_elements = parse_virtual_field_id(f_id)
                    if parsed_elements and parsed_elements[0] == matrix_id:
                        f_id_elements = parsed_elements[1:]
                        field_value = None
                        if not f_id_elements[1].startswith('new'):
                            line_id = int(f_id_elements[1])
                            if f_id_elements[0] == 'cell':
                                cell_date = datetime.datetime.strptime(f_id_elements[2], '%Y%m%d').date()
                                cell_id = cell_pool.search(cr, uid, [(conf['cell_date_property'], '=', cell_date), (conf['cell_inverse_property'], '=', line_id)], limit=1, context=context)
                                if cell_id:
                                    cell = cell_pool.browse(cr, uid, cell_id, context)[0]
                                    field_value = getattr(cell, conf['cell_value_property'])
                            elif f_id_elements[0] == 'res':
                                if line_id:
                                    resource_property = f_id_elements[2]
                                    line = line_pool.browse(cr, uid, line_id, context)
                                    field_value = getattr(line, resource_property).id
                        props.update({f_id: field_value})
            updated_result.append(props)
        if isinstance(ids, (int, long)):
            updated_result = updated_result[0]
        return updated_result
    return read_matrix_virtual_fields



def matrix_write_patch(func):
    """
    """
    def write_matrix_virtual_fields(*arg, **kw):
        result = func(*arg, **kw)
        (obj, cr, uid, ids, vals) = arg[:5]
        context = kw.get('context', None)
        if isinstance(ids, (int, long)):
            ids = [ids]

        written_lines = []
        for report in obj.browse(cr, uid, ids, context):

            # Write one matrix at a time
            for (matrix_id, conf) in get_matrix_conf(obj).items():

                # Get our date ranges
                (date_range, active_date_range) = _get_date_range(report, conf['date_range_property'], conf.get('active_date_range_property', None))

                # Regroup fields by lines
                lines = {}
                for (f_id, f_value) in vals.items():
                    # Ignore non editable matrix cells
                    if not(f_id.startswith('%s_res_' % matrix_id) or f_id.startswith('%s_cell_' % matrix_id)):
                        continue
                    parsed_elements = parse_virtual_field_id(f_id)
                    if parsed_elements and parsed_elements[0] == matrix_id:
                        f_id_elements = parsed_elements[1:]
                        line_id = f_id_elements[1]
                        line_data = lines.get(line_id, {})
                        line_data.update({f_id: f_value})
                        lines[line_id] = line_data

                # Write data of each line
                for (line_id, line_data) in lines.items():
                    # Get line resources
                    line_resources = dict([(parse_virtual_field_id(f_id)[3], int(v)) for (f_id, v) in line_data.items() if f_id.startswith('%s_res_' % matrix_id)])
                    # Check all required resources are provided by the matrix
                    res_ids = set(line_resources.keys())
                    required_res_ids = set([prop_id for (prop_id, prop_type) in conf['line_resource_property_list']])
                    if res_ids != required_res_ids:
                        raise osv.except_osv('Error !', "Line %s resource mismatch: %r provided while we're expecting require %r." % (line_id, res_ids, required_res_ids))
                    # Get line cells
                    line_cells = dict([(datetime.datetime.strptime(parse_virtual_field_id(f_id)[3], '%Y%m%d').date(), v) for (f_id, v) in line_data.items() if f_id.startswith('%s_cell_' % matrix_id)])
                    # Are we updating an existing line or creating a new one ?
                    if line_id.startswith('new'):
                        line_vals = line_resources
                        line_vals.update({conf['line_inverse_property']: report.id})
                        line_id = obj.pool.get(conf['line_type']).create(cr, uid, line_vals, context)
                    line_id = int(line_id)
                    written_lines.append(line_id)

                    # Save cells data
                    for (cell_date, cell_value) in line_cells.items():
                        # Prepare the cell value
                        cell_vals = {
                            conf['cell_value_property']: cell_value,
                            }
                        # Search for an existing cell at the given date
                        cell = obj.pool.get(conf['cell_type']).search(cr, uid, [(conf['cell_date_property'], '=', cell_date), (conf['cell_inverse_property'], '=', line_id)], context=context, limit=1)
                        # Cell doesn't exists, create it
                        if not cell:
                            cell_vals.update({
                                conf['cell_date_property']: cell_date,
                                conf['cell_inverse_property']: line_id,
                                })
                            obj.pool.get(conf['cell_type']).create(cr, uid, cell_vals, context)
                        # Update cell with our data or delete it if it's out of range
                        else:
                            cell_id = cell[0]
                            if cell_date not in active_date_range:
                                obj.pool.get(conf['cell_type']).unlink(cr, uid, [cell_id], context)
                            else:
                                obj.pool.get(conf['cell_type']).write(cr, uid, cell_id, cell_vals, context)

        # If there was no references to one of our line it means it was deleted
        for report in obj.browse(cr, uid, ids, context):
            removed_lines = list(set([l.id for l in _get_prop(report, conf['line_property'])]).difference(set(written_lines)))
            obj.pool.get(conf['line_type']).unlink(cr, uid, removed_lines, context)

        return result

    return write_matrix_virtual_fields
