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
from tools.func import wraps



def _get_prop(obj, prop_name, default_value=None):
    """ Get a property value
    """
    if not prop_name or obj is None:
        return default_value
    prop_value = getattr(obj, prop_name, default_value)
    if prop_value is None:
        raise osv.except_osv('Error !', "%r has no %s property." % (obj, prop_name))
    return prop_value



def _get_date_range(base_object, date_range_property, active_date_range_property, editable_date_range_property):
    """ Utility method to get the displayed date range and the active date range.
        This piece of code was moved in its own method as date range extraction requires some special handling.
    """
    # Get on the current object the date range bounding the timeline
    date_range = _get_prop(base_object, date_range_property)
    # Get the active date range. Default is to let all dates of the displayed range.
    active_date_range = _get_prop(base_object, active_date_range_property, date_range)
    # Get the editable date range. Default is to align this range on the active date range.
    editable_date_range = _get_prop(base_object, editable_date_range_property, active_date_range)

    # date_range and active_date_range values may be stored as text (or selection, which is the same). In this case, we need to evaluate them. It's bad, but it works.
    if isinstance(date_range, (str, unicode)):
        date_range = eval(date_range)
    if isinstance(active_date_range, (str, unicode)):
        active_date_range = eval(active_date_range)
        if not active_date_range:
            active_date_range = date_range
    if isinstance(editable_date_range, (str, unicode)):
        editable_date_range = eval(editable_date_range)
        if not editable_date_range:
            editable_date_range = active_date_range

    # Check the data structure returned by date ranges
    for (range_name, range_data) in [(date_range_property, date_range), (active_date_range_property, active_date_range), (editable_date_range_property, editable_date_range)]:
        if type(range_data) is not type([]):
            raise osv.except_osv('Error !', "%s must return a list of datetime.date objects." % range_name)
        for d in range_data:
            if not isinstance(d, datetime.date):
                raise osv.except_osv('Error !', "%s must return a list of datetime.date objects." % range_name)

    return (date_range, active_date_range, editable_date_range)



def _get_matrix_fields(osv_instance):
    """ Utility method to get all matrix fields defined on the class the provided object is an instance of.
    """
    field_defs = osv_instance.__dict__['_columns']
    matrix_fields = dict([(f_id, f) for (f_id, f) in field_defs.items() if f.__dict__.get('_fnct', None) and getattr(f.__dict__['_fnct'], 'im_class', None) and f.__dict__['_fnct'].im_class.__module__ == globals()['__name__']])
    if not len(matrix_fields):
        return None
    return matrix_fields



def _get_conf(o, matrix_id=None):
    """ Utility method to get the matrix configuration from itself or from any other place.
        The returned configuration is normalized and parsed.
    """
    # Get the matrix field
    matrix_field = o
    if not isinstance(o, matrix):
        matrix_fields = _get_matrix_field(o)
        if matrix_id not in matrix_fields:
            raise osv.except_osv('Error !', "%r matrix field not found on %r." % (matrix_id, o))
        matrix_field = matrix_fields[matrix_id]

    conf = {
        # TODO:
        # Add a visibility option that accept 'hidden', 'readonly', 'editable' (default) or 'inactive'

        # TODO: guess line_type, cell_type and resource_type based on their xxx_property parameter counterparts
        # XXX Haven't found a cleaner way to get my matrix parameters... Any help is welcome ! :)
        # Property name from which we get the lines composing the matrix
        'line_property': matrix_field.__dict__.get('line_property', None),
        'line_type': matrix_field.__dict__.get('line_type', None),
        'line_inverse_property': matrix_field.__dict__.get('line_inverse_property', None),

        # Get line tree definition
        'tree_definition': matrix_field.__dict__.get('tree_definition', None),

        # Widget configuration
        'default_widget_type': matrix_field.__dict__.get('default_widget_type', 'float'),
        'dynamic_widget_type_property': matrix_field.__dict__.get('dynamic_widget_type_property', None),
        'increment_values': matrix_field.__dict__.get('increment_values', [0, 0.5, 1.0]),

        # Property name from which we get the cells composing the matrix.
        # Cells are fetched from the lines as defined above.
        'cell_property': matrix_field.__dict__.get('cell_property', None),
        'cell_type': matrix_field.__dict__.get('cell_type', None),
        'cell_inverse_property': matrix_field.__dict__.get('cell_inverse_property', None),
        'cell_value_property': matrix_field.__dict__.get('cell_value_property', None),
        'cell_date_property': matrix_field.__dict__.get('cell_date_property', None),
        'cell_active_property': matrix_field.__dict__.get('cell_active_property', 'active'),
        'cell_readonly_property': matrix_field.__dict__.get('cell_readonly_property', None),
        'default_cell_value': matrix_field.__dict__.get('default_cell_value', 0.0),

        # Property name of the relation field on which we'll call the date_range property
        'date_range_property': matrix_field.__dict__.get('date_range_property', None),
        'active_date_range_property': matrix_field.__dict__.get('active_date_range_property', None),
        'editable_date_range_property': matrix_field.__dict__.get('editable_date_range_property', None),

        # The format we use to display date labels
        'date_format': matrix_field.__dict__.get('date_format', "%Y-%m-%d"),

        # Add read-only columns at the end of the matrix.
        # It needs a list of dictionnary like this:
        #    [{'label': "Productivity", 'line_property': 'productivity_index', 'hide_value': True},
        #     {'label': "Performance" , 'line_property': 'performance_index' , 'hide_tree_totals': True},
        #    ],
        'additional_columns': matrix_field.__dict__.get('additional_columns', []),

        # Add read-only lines below the matrix
        'additional_line_property':  matrix_field.__dict__.get('additional_line_property', None),

        # If set to true, hide the first column of the table.
        'hide_line_title': matrix_field.__dict__.get('hide_line_title', False),

        # Do not allow the removal of lines
        'hide_remove_line_buttons': matrix_field.__dict__.get('hide_remove_line_buttons', False),

        # Columns and row totals are optionnal
        'hide_column_totals': matrix_field.__dict__.get('hide_column_totals', False),
        'hide_line_totals': matrix_field.__dict__.get('hide_line_totals', False),

        # Set the threshold above which we set a column total in red. Set to None to desactivate the warning threshold.
        'column_totals_warning_threshold': matrix_field.__dict__.get('column_totals_warning_threshold', None),

        # If set to True this option will hide all tree-level add-line selectors.
        'editable_tree': not matrix_field.__dict__.get('non_editable_tree', False),

        # If set to True this option will hide all tree-level add-line selectors.
        'hide_tree': matrix_field.__dict__.get('hide_tree', False),

        # Additional classes can be manually added
        'css_classes': matrix_field.__dict__.get('css_classes', []),

        # TODO
        'experimental_slider': matrix_field.__dict__.get('experimental_slider', False),

        # Force the matrix in read only mode, even in editable mode
        'readonly': matrix_field.__dict__.get('readonly', False),

        # Get the matrix title
        'title': matrix_field.__dict__.get('title', "Lines"),
        }

    # Check that all required parameters are there
    for p_name in ['line_property', 'line_type', 'line_inverse_property', 'tree_definition', 'cell_property', 'cell_type', 'cell_inverse_property', 'cell_value_property', 'cell_date_property']:
        if not conf.get(p_name, None):
            raise osv.except_osv('Error !', "%s parameter is missing." % p_name)

    # tree_definition list required at least one parameter
    if type(conf['tree_definition']) != type([]) or len(conf['tree_definition']) < 1:
        raise osv.except_osv('Error !', "tree_definition parameter must be a list with at least one element.")

    # Normalize parameters
    if conf['hide_tree']:
        conf['editable_tree'] = False
    if conf['experimental_slider']:
        conf['css_classes'] += ['slider']

    return conf



def _get_matrix_fields_conf(obj):
    return dict([(matrix_id, _get_conf(matrix)) for (matrix_id, matrix) in _get_matrix_fields(obj).items()])



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
        conf = _get_conf(self)

        # Browse through all objects on which our matrix field is defined
        matrix_list = {}
        for base_object in obj.browse(cr, uid, ids, context):
            matrix_data = []

            # Get our date ranges
            (date_range, active_date_range, editable_date_range) = _get_date_range(base_object, conf['date_range_property'], conf['active_date_range_property'], conf['editable_date_range_property'])

            # Get the list of all objects new rows of the matrix can be linked to
            # Keep the original order defined in matrix properties
            resource_value_list = []
            for level_def in conf['tree_definition']:
                res_def = level_def.copy()
                res_id = res_def.pop('line_property')
                res_type = res_def.pop('resource_type')
                p = base_object.pool.get(res_type)
                # Compute domain by merging its static and dynamic definition
                res_domain = res_def.pop('domain', []) + _get_prop(base_object, res_def.pop('dynamic_domain_property', None), [])
                # Build up the resource definition
                res_def.update({
                    'id': res_id,
                    'values': [(o.id, self._get_title_or_id(o)) for o in p.browse(cr, uid, p.search(cr, uid, res_domain, context=context), context)],
                    })
                resource_value_list.append(res_def)

            # Browse all lines that will compose our the main part of the matrix
            lines = [(line, 'body') for line in _get_prop(base_object, conf['line_property'], [])]
            # Add bottom lines if provided
            if conf['additional_line_property']:
                lines += [(line, 'bottom') for line in _get_prop(base_object, conf['additional_line_property'], [])]
            for (line, line_position) in lines:
                # Transfer some line data to the matrix widget
                line_data = {
                    'id': line.id,
                    'name': self._get_title_or_id(line),
                    }

                # Is this resource required ?
                # FIX: 'required': getattr(getattr(line, conf['line_resource_property']), 'required', False),

                # By marking lines as required, we implicitely hide its remove button
                if conf['hide_remove_line_buttons']:
                    line_data.update({'required': True})

                # Get the type of the widget we'll use to display cell values
                line_widget = _get_prop(line, conf['dynamic_widget_type_property'], conf['default_widget_type'])
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
                for res in conf['tree_definition']:
                    res_id = res['line_property']
                    resource = _get_prop(line, res_id)
                    res_list.append({
                        'id': res_id,
                        'label': self._get_title_or_id(resource),
                        'value': resource.id,
                        })
                line_data.update({'resources': res_list})

                # Get all cells of the line, indexed by their IDs
                cells = dict([(cell.id, cell) for cell in _get_prop(line, conf['cell_property'], [])])

                # Provide to the matrix a cell for each active date in the range
                cells_data = {}
                for d in active_date_range:
                    # Find a cell corresponding to the date in the date_range
                    cell = None
                    for (cell_id, cell) in cells.items():
                        cell_date = datetime.datetime.strptime(_get_prop(cell, conf['cell_date_property']), '%Y-%m-%d').date()
                        if cell_date == d:
                            break
                    cell_value = _get_prop(cell, conf['cell_value_property'], conf['default_cell_value'])
                    # Skip the cell to hide it if its active property is True
                    active_cell = _get_prop(cell, conf['cell_active_property'], True)
                    if not active_cell:
                        continue
                    # Pop the cell ID to mark it as consumed (this will prevent it to be automatticaly removed later)
                    if cell is not None:
                        cells.pop(cell_id)
                    # Set cell editability according its dynamic property.
                    read_only_cell = _get_prop(cell, conf['cell_readonly_property'], False)
                    if line_data.get('read_only', False):
                        # If the line is readonly then the cell is force to readonly.
                        read_only_cell = True
                    elif d not in editable_date_range:
                        # Column-level options override cells-level visibility properties
                        read_only_cell = True
                    # Pack all properties of the cell
                    cells_data[d.strftime('%Y%m%d')] = {
                        'value': cell_value,
                        'read_only': read_only_cell,
                        }

                line_data.update({'cells_data': cells_data})
                # Remove all out of date, duplicate cells and inactive cells
                obj.pool.get(conf['cell_type']).unlink(cr, uid, cells.keys(), context)

                # Get data of additional columns
                for line_property in [c['line_property'] for c in conf['additional_columns'] if 'line_property' in c]:
                    if line_property in line_data['cells_data']:
                        raise osv.except_osv('Error !', "Additional line property %s conflicts with matrix column ID." % line_property)
                    v = _get_prop(line, line_property)
                    if type(v) != type(0.0):
                        v = float(v)
                    line_data['cells_data'].update({line_property: {
                        'value': v,
                        'read_only': True,
                        }})

                matrix_data.append(line_data)

            # Get default cells and their values for the template row.
            template_cells_data = {}
            for d in active_date_range:
                # Set the editability of the cell
                read_only_cell = False
                if d not in editable_date_range:
                    read_only_cell = True
                template_cells_data[self._date_to_str(d)] = {
                    'value': conf['default_cell_value'],
                    'read_only': read_only_cell,
                    }
            template_resources = [{
                    'id': res['line_property'],
                    'label': res['line_property'].replace('_', ' ').title(),
                    'value': 0,
                    } for res in conf['tree_definition']]
            # Add a row template at the end
            template_line_data = {
                'id': "template",
                'name': "Row template",
                'widget': conf['default_widget_type'],
                'cells_data': template_cells_data,
                'resources':template_resources,
                }
            if conf['hide_remove_line_buttons']:
                template_line_data.update({'required': True})
            matrix_data.append(template_line_data)

            # Pack all data required to render the matrix
            matrix_def = conf
            matrix_def.update({
                'matrix_data': matrix_data,
                'date_range': [self._date_to_str(d) for d in date_range],  # Format our date range for our matrix # XXX Keep them as date objects ?
                'resource_value_list': resource_value_list,
                })

            matrix_list.update({base_object.id: matrix_def})
        return matrix_list



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

    @wraps(func)
    def read_matrix_virtual_fields(*arg, **kw):
        result = func(*arg, **kw)
        (obj, cr, uid, ids, fields) = arg[:5]
        context = kw.get('context', None)
        if isinstance(ids, (int, long)):
            result = [result]
        updated_result = []
        for props in result:
            unread_fields = set(fields).difference(set(props.keys()))
            for (matrix_id, conf) in _get_matrix_fields_conf(obj).items():
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

    @wraps(func)
    def write_matrix_virtual_fields(*arg, **kw):
        result = func(*arg, **kw)
        (obj, cr, uid, ids, vals) = arg[:5]
        context = kw.get('context', None)
        if isinstance(ids, (int, long)):
            ids = [ids]

        written_lines = []
        for report in obj.browse(cr, uid, ids, context):

            # Write one matrix at a time
            for (matrix_id, conf) in _get_matrix_fields_conf(obj).items():

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

                # No matrix data was edited on that matrix, so skip updating it
                if not lines:
                    continue

                # Get our date ranges
                (date_range, active_date_range, editable_date_range) = _get_date_range(report, conf['date_range_property'], conf['active_date_range_property'], conf['editable_date_range_property'])

                # Write data of each line
                for (line_id, line_data) in lines.items():
                    # Get line resources
                    line_resources = dict([(parse_virtual_field_id(f_id)[3], int(v)) for (f_id, v) in line_data.items() if f_id.startswith('%s_res_' % matrix_id)])
                    # Check all required resources are provided by the matrix
                    res_ids = set(line_resources.keys())
                    required_res_ids = set([prop['line_property'] for prop in conf['tree_definition']])
                    if res_ids != required_res_ids:
                        raise osv.except_osv('Error !', "Line %s resource mismatch: %r provided while we're expecting %r." % (line_id, res_ids, required_res_ids))
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
                        # Transform the value to a float, if the user has entered nothing just use the default value
                        cell_value = ''.join([c for c in cell_value if c.isdigit() or c in ['-', '.', ',']]).replace(',', '.')
                        try:
                            cell_value = float(cell_value)
                        except ValueError:
                            cell_value = conf['default_cell_value']
                        cell_vals = {
                            conf['cell_value_property']: cell_value,
                            }
                        # Search for an existing cell at the given date
                        cell_pool = obj.pool.get(conf['cell_type'])
                        cell_ids = cell_pool.search(cr, uid, [(conf['cell_date_property'], '=', cell_date), (conf['cell_inverse_property'], '=', line_id)], context=context, limit=1)
                        # Cell doesn't exists, create it
                        if not cell_ids:
                            cell_vals.update({
                                conf['cell_date_property']: cell_date,
                                conf['cell_inverse_property']: line_id,
                                })
                            cell_pool.create(cr, uid, cell_vals, context)
                        # Update or delete the cell
                        else:
                            cell_id = cell_ids[0]
                            # Compute the active state of the cell
                            cell = cell_pool.browse(cr, uid, cell_id, context)
                            active_cell = _get_prop(cell, conf['cell_active_property'], True)
                            if cell_date not in active_date_range:
                                active_cell = False
                            # Update cell with our data or delete it if it's not active
                            if not active_cell:
                                cell_pool.unlink(cr, uid, cell_id, context)
                            else:
                                cell_pool.write(cr, uid, cell_id, cell_vals, context)

                # If there was no references to one of our line it means it was deleted
                removed_lines = list(set([l.id for l in _get_prop(report, conf['line_property'])]).difference(set(written_lines)))
                report.pool.get(conf['line_type']).unlink(cr, uid, removed_lines, context)

        return result

    return write_matrix_virtual_fields
