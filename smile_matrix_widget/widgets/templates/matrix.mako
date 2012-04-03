<%!
    import datetime
    import simplejson as json
%>


<%def name="render_float(f)">
<%
    if type(f) != type(0.0):
        f = float(f)
    if int(f) == f:
        f = int(f)
    return f
%>
</%def>


<%def name="render_resources(line)">
    <%
        read_only = line.get('read_only', False)
    %>
    <td class="resource">
        <%
            resources = line.get('resources', [])
        %>
        <span class="name">${resources[-1]['label']}</span>
        %if editable_mode and not read_only:
            %for res in resources:
                <%
                    res_id = res['id']
                    res_label = res['label']
                    res_value = res['value']
                    res_field_id = "%s__res_%s_%s" % (name, line['id'], res_id)
                %>
                <input type="hidden" id="${res_field_id}" name="${res_field_id}" value="${res_value}" title="${res_label}"/>
            %endfor
        %endif
    </td>
</%def>


<%def name="render_cell(cell_def, cell_id=None, widget='float', css_classes=[])">
    <%
        if cell_def is None:
            cell_def = {}
        cell_value = cell_def.get('value', None)
        cell_editable = editable_mode
        if cell_def.get('read_only', False):
            cell_editable = False
    %>
    <td
        %if cell_id and (not cell_editable or cell_value is None):
            id="${cell_id}"
        %endif
        class="${' '.join(css_classes)}
        % if not editable_mode:
            %if not cell_value:
                zero
            %elif cell_value < 0.0:
                negative
            %endif
        %endif
        "
        >
        %if cell_value is not None:
            %if cell_editable:
                %if widget == 'boolean':
                    <input type="hidden" kind="boolean" name="${cell_id}" id="${cell_id}" value="${cell_value and '1' or '0'}"/>
                    <input type="checkbox" enabled="enabled" kind="boolean" class="checkbox" id="${cell_id}_checkbox_"
                        %if cell_value:
                            checked="checked"
                        %endif
                    />
                %elif widget == 'selection':
                    <select kind="float" name="${cell_id}" id="${cell_id}" class="${widget}">
                        %for v in cell_def.get('value_range', []):
                            <option value="${v}" ${py.selector(float(cell_value) == float(v))}>${v}</option>
                        %endfor
                    </select>
                %else:
                    <input type="text" kind="float" name="${cell_id}" id="${cell_id}" value="${render_float(cell_value)}" size="1" class="${widget}"/>
                %endif
            %else:
                %if widget == 'boolean':
                    <input type="checkbox" name="${cell_id}" id="${cell_id}" kind="boolean" class="checkbox" readonly="readonly" disabled="disabled" value="${cell_value and '1' or '0'}"
                        %if cell_value:
                            checked="checked"
                        %endif
                    />
                %else:
                    ${render_float(cell_value)}
                %endif
            %endif
        %endif
    </td>
</%def>


<%def name="render_additional_column_cell(columns, line, position='right')">
    %for (line_property_cell, col_def) in [(line.get('cells_data', dict()).get(c['line_property'], {}), c) for c in [col for col in columns if col.get('position', 'right') == position] if 'line_property' in c]:
        <%
            if col_def.get('hide_value', False):
                line_property_cell.update({'value': None})
        %>
        ${render_cell(line_property_cell)}
    %endfor
</%def>


<%def name="render_line(line, date_range, level=1)">
    <%
        line_readonly = line.get('read_only', False)
        line_removable = line.get('removable', True)
        line_widget = line.get('widget', 'float')
    %>
    <tr class="level level_${level} widget_${line_widget}
        %if line['id'] == 'template':
            template
        %endif
        %if line_readonly:
            read_only
        %endif
        "
        %if not line_readonly:
            id="${'%s__line_%s' % (name, line['id'])}"
        %endif
        >

        %if line_widget in ['spacer', 'header']:

            <%
                colspan_lenght = 2 + len(date_range) + len(value['additional_columns']) + navigation + (not hide_line_totals)
            %>
            <td colspan="${colspan_lenght}">
                %if line_widget == 'header':
                    ${line.get('name', 'Header')}
                %endif
            </td>

        %else:

            ${render_resources(line)}

            ${render_additional_column_cell(value['additional_columns'], line, position='left')}

            <td class="delete_line">
                %if editable_mode and line_removable:
                    <span class="button delete_row">&#10006;</span>
                %endif
            </td>

            %for date in date_range:
                <%
                    cell_id = '%s__cell_%s_%s' % (name, line['id'], date)
                    cell_def = line.get('cells_data', {}).get(date, None)
                %>
                ${render_cell(cell_def, cell_id, line_widget)}
            %endfor

            %if navigation:
                <td></td>
            %endif

            %if not hide_line_totals:
                <%
                    row_total = sum([v['value'] for (k, v) in line.get('cells_data', dict()).items() if k in date_range])
                    row_total_cell_id = not read_only and "%s__row_total_%s" % (name, line['id']) or None
                    row_total_cell = {
                        'value': row_total,
                        'read_only': True,
                        }
                %>
                ${render_cell(row_total_cell, cell_id=row_total_cell_id, css_classes=['total'])}
            %endif

            ${render_additional_column_cell(value['additional_columns'], line, position='right')}

        %endif
    </tr>
</%def>


<%def name="render_resource_selector(res_def)">
    <%
        res_id = res_def.get('id', None)
        res_values = res_def.get('values', [])
        res_editable = res_def.get('editable', True)
        selector_id = "%s__res_list_%s" % (name, res_id)
    %>
    %if len(res_values) and editable_mode and res_editable:
        <span class="resource_values">
            <select id="${selector_id}" kind="char" name="${selector_id}" type2="" operator="=" class="selection_search selection">
                <option value="default" selected="selected">&mdash; Select here new line's resource &mdash;</option>
                %for (res_value, res_label) in res_values:
                    <option value="${res_value}">${res_label}</option>
                %endfor
            </select>
            <span class="button add_row">&#10010;</span>
        </span>
    %endif
</%def>


<%def name="render_sub_matrix_header(level_res, res_values, level, date_range, sub_lines=[], css_class=None, show_selector=True)">
    <%
        # Build a virtual line to freeze resources at that level
        virtual_line = {
            'id': 'dummy%s' % value['row_uid'],
            'resources': level_res,
            }
        value['row_uid'] += 1
    %>
    <tr id="${'%s__line_%s' % (name, virtual_line['id'])}" class="resource_line level level_${level}
        %if css_class:
            ${css_class}
        %endif
        ">

        ${render_resources(virtual_line)}

        ${render_additional_column_subtotals(value['additional_columns'], sub_lines, position='left')}

        %if show_selector and len(res_values.get('values', [])) and editable_mode and res_values.get('editable', True):
            <%
                colspan_lenght = 1
                if navigation:
                    colspan_lenght += 1
                if navigation and len(date_range) > 10:
                    colspan_lenght += 10
                else:
                    colspan_lenght += len(date_range)
            %>
            <td colspan="${colspan_lenght}" class="resource_selector">
                ${render_resource_selector(res_values)}
            </td>
        %else:
            <td class="delete_line"></td>

            %for date in date_range:
                <%
                    date_column_sum_cell = {
                        'value': sum([line.get('cells_data', dict()).get(date, {}).get('value', 0.0) for line in sub_lines]),
                        'read_only': True,
                        }
                    cell_id = '%s__cell_%s_%s' % (name, virtual_line['id'], date)
                %>
                ${render_cell(date_column_sum_cell, cell_id)}
            %endfor

            %if navigation:
                <td></td>
            %endif

        %endif

        %if not hide_line_totals:
            <%
                row_total = []
                for line in sub_lines:
                    row_total += [v['value'] for (k, v) in line.get('cells_data', dict()).items() if k in date_range]
                row_total_cell = {
                    'value': sum(row_total),
                    'read_only': True,
                    }
                row_total_cell_id = "%s__row_total_%s" % (name, virtual_line['id'])
            %>
            ${render_cell(row_total_cell, cell_id=row_total_cell_id, css_classes=['total'])}
        %endif

        ${render_additional_column_subtotals(value['additional_columns'], sub_lines, position='right')}

    </tr>
</%def>


<%def name="render_sub_matrix(lines, resource_value_list, date_range, level=1, level_resources=[], editable_tree=True, hide_tree=False)">
    %if level < len(resource_value_list):
        <%
            res_def = resource_value_list[level - 1]
            res_id = res_def.get('id', None)
            res_values = res_def.get('values', [])
        %>
        %for (res_value, res_label) in res_values:
            <%
                level_res = level_resources + [{
                    'id': res_id,
                    'label': res_label,
                    'value': res_value,
                    }]
                sub_lines = []
                for line in lines:
                    matching_resources = [r for r in line.get('resources', dict()) if r['id'] == res_id and r['value'] == res_value]
                    if len(matching_resources):
                        sub_lines.append(line)
            %>
            %if len(sub_lines):
                %if not hide_tree:
                    ${render_sub_matrix_header(level_res, resource_value_list[level], level, date_range, sub_lines, show_selector=editable_tree)}
                %endif
                ${render_sub_matrix(sub_lines, resource_value_list, date_range, level + 1, level_res, editable_tree=editable_tree, hide_tree=hide_tree)}
            %endif
        %endfor
    %endif
    %if level == len(resource_value_list):
        %for line in lines:
            ${render_line(line, date_range, level)}
        %endfor
    %endif
</%def>


<%def name="render_additional_column_titles(columns, position='right')">
    %for (i, c) in enumerate([col for col in columns if col.get('position', 'right') == position]):
        <th>${c.get('label', "Additional %s column #%s" % (position, i))}</th>
    %endfor
</%def>


<%def name="render_additional_column_subtotals(columns, sub_lines, position='right')">
    %for col_def in [c for c in [col for col in columns if col.get('position', 'right') == position] if 'line_property' in c]:
        <%
            additional_sum_cell = {
                'value': None,
                'read_only': True,
            }
            if not col_def.get('hide_tree_totals', False):
                additional_sum_cell.update({'value': sum([line.get('cells_data', dict()).get(col_def['line_property'], {}).get('value', 0.0) for line in sub_lines])})
        %>
        ${render_cell(additional_sum_cell)}
    %endfor
</%def>


<%def name="render_additional_column_totals(columns, body_lines, position='right')">
    %for line_property in [c['line_property'] for c in [col for col in columns if col.get('position', 'right') == position] if 'line_property' in c]:
        <%
            additional_sum_cell = {
                'value': sum([line.get('cells_data', dict()).get(line_property, {}).get('value', 0.0) for line in body_lines]),
                'read_only': True,
                }
        %>
        ${render_cell(additional_sum_cell, css_classes=['total'])}
    %endfor
</%def>


<%
    css_classes = ''
    if value is not None:
        css_classes = ' '.join(value.get('css_classes', []))
%>


<div id="${name}" class="matrix ${css_classes}">

    %if type(value) == type({}) and 'date_range' in value:

        <%
            # Initialize our global new row UID
            value['row_uid'] = 1

            # Merge readonly with editable property
            editable_mode = editable and not readonly
            if value.get('read_only', None):
                editable_mode = False

            # Extract some basic information
            lines = value.get('matrix_data', [])
            top_lines    = [l for l in lines if l.get('position', 'body') == 'top']
            bottom_lines = [l for l in lines if l.get('position', 'body') == 'bottom']
            body_lines   = [l for l in lines if l.get('position', 'body') not in ['top', 'bottom']]

            resource_value_list = value['resource_value_list']
            increment_values = value['increment_values']
            date_range = value['date_range']
            date_format = value['date_format']
            hide_line_title = value['hide_line_title']
            hide_column_totals = value['hide_column_totals']
            hide_line_totals = value['hide_line_totals']
            column_totals_warning_threshold = value['column_totals_warning_threshold']
            editable_tree = value['editable_tree']
            hide_tree = value['hide_tree']
            navigation = value['navigation']
        %>

        <style type="text/css">
            /* Reset OpenERP default styles */
            .matrix table thead th {
                font-size: inherit;
            }

            .matrix table tfoot td {
                font-weight: normal;
            }

            .matrix table th {
                text-transform: none;
                border-bottom: 0;
            }

            .item .matrix input {
                min-width: inherit;
            }

            .item .matrix select {
                min-width: inherit;
                width: inherit;
            }

            div.non-editable .matrix table td {
                border: 0;
            }


            /* Set our matrix style */

            .matrix .toolbar {
                margin-bottom: 1em;
            }

            .matrix .zero {
                color: #ccc;
            }

            .matrix .negative {
                color: #f00;
            }

            .matrix .template {
                display: none;
            }

            .matrix .navigation.disabled .button {
                display: none;
            }

            .matrix th,
            .matrix .total,
            .matrix .total td,
            .matrix .widget_header {
                font-weight: bold;
                background-color: #ddd;
            }

            .matrix td.warning {
                background: #f00;
                color: #fff;
            }

            .matrix table {
                text-align: center;
                margin-top: 1em;
                margin-bottom: 1em;
                %if navigation:
                    width: 100%;
                %endif
            }

            .matrix input,
            .matrix table .button {
                text-align: center;
            }

            .matrix table .resource,
            .matrix table .resource_selector {
                text-align: left;
            }

            .matrix table .resource_selector {
                white-space: nowrap;
            }

            %if hide_line_title:
                #${name}.matrix table .resource {
                    display: none;
                }
            %endif

            .matrix table .button {
                display: inline-block;
                padding: .3em;
                min-width: 2.2em;
            }

            .matrix table .button.delete_row {
                font-weight: bold;
                min-width: 1em;
                height: 1em;
            }

            .matrix table .button.delete_row:hover {
                background: #fc3223;
            }

            .matrix td, div.non-editable .matrix table td,
            .matrix th, div.non-editable .matrix table th {
                height: 2em;
                min-width: 2.2em;
                margin: 0;
                padding: 0 .1em;
                border-top: 1px solid #ccc;
            }

            .matrix th, div.non-editable .matrix table th {
                padding-right: .3em;
                padding-left: .3em;
            }

            .matrix th.resource, div.non-editable .matrix table th.resource {
                padding-right: .1em;
                padding-left: .1em;
            }

            .matrix table,
            .matrix table tfoot .total td {
                border-bottom: 1px solid #ccc;
            }

            %if not hide_tree:
                %for i in range(1, len(resource_value_list)):
                    #${name}.matrix tbody tr.level_${i} td, div.non-editable .matrix table tbody tr.level_${i} td {
                        border-top-width: ${len(resource_value_list) - i + 1}px;
                    }
                    #${name}.matrix .level_${i+1} td.resource,
                    #${name}.matrix .level_${i+1} td.resource_selector,
                    #${name}.matrix .level_${i+1} td.delete_line {
                        padding-left: ${i}em;
                    }
                %endfor
            %endif

            ${value.get('custom_css', None)}

        </style>

        %if value.get('custom_js', None):
            <script type="text/javascript">
            <!--
                ${value['custom_js']|n}
            -->
            </script>
        %endif

        %if editable_mode:
            <div class="toolbar level level_0">
                %if editable_tree:
                    ${render_resource_selector(resource_value_list[0])}
                %endif
                <span id="matrix_button_template" class="button increment template">
                    Button template
                </span>
                <input type="hidden" id="${"%s__increment_values" % name}" value="${json.dumps(increment_values)}" title="Increment button values"/>
                %if column_totals_warning_threshold is not None:
                    <input type="hidden" id="${"%s__column_warning_threshold" % name}" value="${column_totals_warning_threshold}" title="Column warning threshold"/>
                %endif
                <input type="text" kind="char" name="${"%s__line_removed" % name}" id="${"%s__line_removed" % name}" value="" title="ID list of removed lines" style="display: none;"/>
            </div>
        %endif

        <table>
            <thead>
                <tr>
                    <th class="resource">${value['title']}</th>
                    ${render_additional_column_titles(value['additional_columns'], position='left')}
                    <th id="${"%s__previous" % name}" class="navigation disabled">
                        %if navigation:
                            <span class="button" title="Previous">&lsaquo;&lsaquo;</span>
                        %endif
                    </th>
                    %for date in date_range:
                        <th id="${"%s__column_label_%s" % (name, date)}">${datetime.datetime.strptime(date, '%Y%m%d').strftime(str(date_format))}</th>
                    %endfor
                    %if navigation:
                        <th id="${"%s__next" % name}" class="navigation"><span class="button" title="Next">&rsaquo;&rsaquo;</span></th>
                    %endif
                    %if not hide_line_totals:
                        <th class="total">${value['total_label']}</th>
                    %endif
                    ${render_additional_column_titles(value['additional_columns'], position='right')}
                </tr>
            </thead>
            <tfoot>
                %if not hide_column_totals:
                    <tr class="total">
                        <td class="resource">${value['total_label']}</td>
                        ${render_additional_column_totals(value['additional_columns'], body_lines, position='left')}
                        <td></td>
                        %for date in date_range:
                            <%
                                column_values = [line['cells_data'][date]['value'] for line in body_lines if (date in line.get('cells_data', dict())) and (line['widget'] not in ['header', 'spacer'])]
                                column_total_cell_id = "%s__column_total_%s" % (name, date)
                            %>
                            %if len(column_values):
                                <%
                                    column_total = sum(column_values)
                                    column_total_css_classes = []
                                    if column_totals_warning_threshold is not None and column_total > column_totals_warning_threshold:
                                        column_total_css_classes.append('warning')
                                    column_total_cell = {
                                        'value': column_total,
                                        'read_only': True,
                                        }
                                %>
                                ${render_cell(column_total_cell, cell_id=column_total_cell_id, css_classes=column_total_css_classes)}
                            %else:
                                <td id="${column_total_cell_id}"></td>
                            %endif
                        %endfor
                        %if navigation:
                            <td></td>
                        %endif
                        %if not hide_line_totals:
                            <%
                                grand_total_cell = {
                                    'value': sum([sum([v['value'] for (k, v) in line['cells_data'].items() if k in date_range]) for line in body_lines if line['widget'] not in ['header', 'spacer'] ]),
                                    'read_only': True,
                                    }
                                grand_total_cell_id = "%s__grand_total" % name
                            %>
                            ${render_cell(grand_total_cell, cell_id=grand_total_cell_id)}
                        %endif
                        ${render_additional_column_totals(value['additional_columns'], body_lines, position='right')}
                    </tr>
                %endif
                %for line in bottom_lines:
                    ${render_line(line, date_range)}
                %endfor
            </tfoot>
            <tbody>
                <%
                    template_line = [l for l in lines if l['id'] == 'template'][0]
                    non_templates_lines = [l for l in body_lines if l['id'] != 'template']
                %>
                ${render_sub_matrix(non_templates_lines, resource_value_list, date_range, editable_tree=editable_tree, hide_tree=hide_tree)}

                %if editable_tree:
                    <%doc>
                        Render a sub-matrix header template for each level of resource.
                        Level 0 is skipped as it's already rendered outside of the matrix table.
                    </%doc>
                    <%
                        level_res = []
                    %>
                    %for (res_index, res_def) in enumerate(resource_value_list):
                        %if res_index != 0:
                            ${render_sub_matrix_header(level_res, res_def, res_index, date_range, css_class='template')}
                        %endif
                        <%
                            res_id = res_def.get('id', None)
                            level_res.append({
                                'id': res_id,
                                'label': '%s template label' % res_id,
                                'value': 0,
                                })
                        %>
                    %endfor
                    <%doc>
                        Render a template float line to help the interactive Javascript code render consistent stuff.
                    </%doc>
                    ${render_line(template_line, date_range, level=len(resource_value_list))}
                %endif
            </tbody>
        </table>

    %else:

        Can't render the matrix widget, not enough data provided.

    %endif

</div>
