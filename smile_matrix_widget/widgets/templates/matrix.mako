<%!
    import datetime
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
    <td class="resource">
        <%
            resources = line.get('resources', [])
        %>
        <span class="name">${resources[-1]['label']}</span>
        %if editable:
            %for res in resources:
                <%
                    res_id = res['id']
                    res_label = res['label']
                    res_value = res['value']
                    res_field_id = "res_%s_%s" % (line['id'], res_id)
                %>
                <input type="hidden" id="${res_field_id}" name="${res_field_id}" value="${res_value}" title="${res_label}"/>
            %endfor
        %endif
    </td>
</%def>


<%def name="render_float_line(line, date_range, level=1)">
    <tr id="${'line_%s' % line['id']}" class="level level_${level}
        %if line['id'] == 'template':
            template
        %endif
        ">
        ${render_resources(line)}
        <td class="delete_line">
            %if editable and not line.get('required', False):
                <span class="button delete_row">X</span>
            %endif
        </td>
        %for date in date_range:
            <td class="float">
                <%
                    cell_id = 'cell_%s_%s' % (line['id'], date)
                    cell_value = line.get('cells_data', {}).get(date, None)
                %>
                %if cell_value is not None:
                    %if editable:
                        <input type="text" kind="float" name="${cell_id}" id="${cell_id}" value="${render_float(cell_value)}" size="1" class="${line['widget']}"/>
                    %else:
                        <span kind="float" id="${cell_id}" value="${render_float(cell_value)}"
                            %if not editable and cell_value <= 0.0:
                                class="zero"
                            %endif
                            >
                                ${render_float(cell_value)}
                        </span>
                    %endif
                %endif
            </td>
        %endfor
        <%
            row_total = sum([v for (k, v) in line.get('cells_data', dict()).items()])
        %>
        <td class="total"
            id="row_total_${line['id']}"
            %if not editable and row_total <= 0.0:
                class="zero"
            %endif
            >
            ${render_float(row_total)}
        </td>
    </tr>
</%def>


<%def name="render_resource_selector(res_def)">
    <%
        res_id = res_def.get('id', None)
        res_values = res_def.get('values', [])
        selector_id = "resource_list_%s" % res_id
    %>
    %if len(res_values) and editable:
        <span class="resource_values">
            <select id="${selector_id}" kind="char" name="${selector_id}" type2="" operator="=" class="selection_search selection">
                <option value="default" selected="selected">&mdash; Select here new line's resource &mdash;</option>
                %for (res_value, res_label) in res_values:
                    <option value="${res_value}">${res_label}</option>
                %endfor
            </select>
            <span class="button add_row">+</span>
        </span>
    %endif
</%def>


<%def name="render_sub_matrix_header(level_res, res_values, level, date_range, css_class=None)">
    <%
        # Build a virtual line to freeze resources at that level
        virtual_line = {
            'id': 'dummy%s' % value['row_uid'],
            'resources': level_res,
            }
        value['row_uid'] += 1
    %>
    <tr class="resource level level_${level}
        %if css_class:
            ${css_class}
        %endif
        ">
        ${render_resources(virtual_line)}
        <td colspan="${len(date_range) + 2}" class="resource_selector">
            ${render_resource_selector(res_values)}
        </td>
    </tr>
</%def>


<%def name="render_sub_matrix(lines, resource_value_list, date_range, level=1, level_resources=[])">
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
                    matching_resources = [r for r in line.get('resources') if r['id'] == res_id and r['value'] == res_value]
                    if len(matching_resources):
                        sub_lines.append(line)
            %>
            %if len(sub_lines):
                ${render_sub_matrix_header(level_res, resource_value_list[level], level, date_range)}
                ${render_sub_matrix(sub_lines, resource_value_list, date_range, level + 1, level_res)}
            %endif
        %endfor
    %endif
    %if level == len(resource_value_list):
        %for line in lines:
            ${render_float_line(line, date_range, level)}
        %endfor
    %endif
</%def>


<%
    css_classes = ''
    if value is not None:
        css_classes = ' '.join(value.get('class', []))
%>


<div class="matrix ${css_classes}">

    %if type(value) == type({}) and 'date_range' in value:

        <%
            # Initialize our global new row UID
            value['row_uid'] = 1
            # Extract some basic information
            lines = value.get('matrix_data', [])
            column_date_label_format = value.get('column_date_label_format', '%Y-%m-%d')
            resource_value_list = value.get('resource_value_list', [])
        %>

        <style type="text/css">
            /* Reset OpenERP default styles */
            .matrix table tfoot td {
                font-weight: normal;
            }

            .matrix table th {
                text-transform: none;
            }

            .item .matrix input,
            .item .matrix select {
                width: inherit;
                min-width: inherit;
            }


            /* Set our style */

            .matrix .toolbar {
                margin-bottom: 1em;
            }

            .matrix select {
                width: 30em;
            }

            .matrix .zero {
                color: #ccc;
            }

            .matrix .warning {
                background: #f00;
                color: #fff;
            }

            .matrix .template {
                display: none;
            }

            .matrix .total,
            .matrix .total td {
                font-weight: bold;
            }

            .matrix table {
                text-align: center;
                margin-bottom: 1em;
            }

            .matrix input {
                text-align: center;
            }

            .matrix table .resource {
                text-align: left;
            }

            .matrix table .button.delete_row,
            .matrix table .button.increment {
                display: block;
                padding: .3em;
            }

            .matrix td,
            .matrix th {
                min-width: 2.2em;
                height: 1.5em;
            }

            %for i in range(1, len(resource_value_list)):
                .matrix .level_${i+1} td.resource,
                .matrix .level_${i+1} td.resource_selector,
                .matrix .level_${i+1} td.delete_line {
                    padding-left: ${i}em;
                }
            %endfor

            .matrix table tbody td,
            div.non-editable .matrix table tbody td,
            .matrix table th,
            .matrix table tfoot tr.boolean_line td {
                border-style: solid;
                border-color: #ccc;
                margin: 0;
                padding: 0 .1em;
            }
            .matrix table tbody td,
            div.non-editable .matrix table tbody td,
            .matrix table th {
                border-width: 0 0 1px;
            }
            .matrix table tfoot tr.boolean_line td {
                border-width: 1px 0 0;
            }
        </style>

        %if editable:
            <div class="toolbar level level_0">
                ${render_resource_selector(resource_value_list[0])}
                <span id="matrix_button_template" class="button increment template">
                    Button template
                </span>
            </div>
        %endif

        <table id="${name}">
            <thead>
                <tr>
                    <th class="resource">Line</th>
                    <th></th>
                    %for date in value['date_range']:
                        <th>${datetime.datetime.strptime(date, '%Y%m%d').strftime(column_date_label_format)}</th>
                    %endfor
                    <th class="total">Total</th>
                </tr>
            </thead>
            <tfoot>
                <tr class="total">
                    <td class="resource">Total</td>
                    <td></td>
                    %for date in value['date_range']:
                        <%
                            column_values = [line['cells_data'][date] for line in lines if line['widget'] != 'boolean' and date in line['cells_data']]
                        %>
                        %if len(column_values):
                            <%
                                column_total = sum(column_values)
                            %>
                            <td id="column_total_${date}" class="
                                %if not editable and column_total <= 0.0:
                                    zero
                                %endif
                                %if column_total > 1:
                                    warning
                                %endif
                                ">
                                ${render_float(column_total)}
                        %else:
                            <td>
                        %endif
                        </td>
                    %endfor
                    <%
                        grand_total = sum([sum([v for (k, v) in line['cells_data'].items()]) for line in lines if line['widget'] != 'boolean'])
                    %>
                    <td id="grand_total"
                        %if not editable and grand_total <= 0.0:
                            class="zero"
                        %endif
                        >
                        ${render_float(grand_total)}
                    </td>
                </tr>
                %for line in [l for l in lines if l['widget'] == 'boolean']:
                    <tr id="${'line_%s' % line['id']}" class="boolean_line">
                        ${render_resources(line)}
                        <td></td>
                        %for date in value['date_range']:
                            <td class="boolean">
                                <%
                                    cell_id = 'cell_%s_%s' % (line['id'], date)
                                    cell_value = line['cells_data'].get(date, None)
                                %>
                                %if cell_value is not None:
                                    %if editable:
                                        <input type="hidden" kind="boolean" name="${cell_id}" id="${cell_id}" value="${cell_value and '1' or '0'}"/>
                                        <input type="checkbox" enabled="enabled" kind="boolean" class="checkbox" id="${cell_id}_checkbox_"
                                            %if cell_value:
                                                checked="checked"
                                            %endif
                                        />
                                    %else:
                                        <input type="checkbox" name="${cell_id}" id="${cell_id}" kind="boolean" class="checkbox" readonly="readonly" disabled="disabled" value="${cell_value and '1' or '0'}"
                                            %if cell_value:
                                                checked="checked"
                                            %endif
                                        />
                                    %endif
                                %endif
                            </td>
                        %endfor
                        <%
                            row_total = sum([v for (k, v) in line.get('cells_data', dict()).items()])
                        %>

                        <td class="total"
                            id="row_total_${line['id']}"
                            %if not editable and row_total <= 0.0:
                                class="zero"
                            %endif
                            >
                            ${render_float(row_total)}
                        </td>
                    </tr>
                %endfor
            </tfoot>
            <tbody>
                <%
                    template_line = [l for l in lines if l['id'] == 'template'][0]
                    non_boolean_lines = [l for l in lines if l['id'] != 'template' and l['widget'] != 'boolean']
                    date_range = value['date_range']
                %>
                ${render_sub_matrix(non_boolean_lines, resource_value_list, date_range)}

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
                ${render_float_line(template_line, date_range, level=len(resource_value_list))}
            </tbody>
        </table>

    %else:

        Can't render the matrix widget, unless a period is selected.

    %endif

</div>