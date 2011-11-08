<%
    import datetime
%>

<style type="text/css">
    /* Reset OpenERP default styles */
    .matrix table tfoot td {
        font-weight: normal;
    }

    .matrix table th {
        text-transform: none;
    }

    .item .matrix input {
        width: inherit;
        min-width: inherit;
    }


    /* Set our style */

    .matrix .toolbar {
        margin-bottom: 1em;
    }

    .matrix .toolbar select {
        width: 30em;
    }

    .matrix .zero {
        color: #ccc;
    }

    .matrix .warning {
        background: #f00;
        color: #fff;
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

    .matrix td,
    .matrix th {
        min-width: 2.2em;
        height: 1.5em;
    }

    .matrix table span {
        display: block;
        padding: .3em;
    }

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


<%def name="render_float(f)">
<%
    if type(f) != type(0.0):
        f = float(f)
    if int(f) == f:
        f = int(f)
    return f
%>
</%def>


<%def name="render_resource(line)">
    <td class="resource">
        <%
            res_field_id = "res_%s" % line['id']
        %>
        <span class="name">${line['name']}</span>
        %if editable:
            <input type="hidden" id="${res_field_id}" name="${res_field_id}" value="${line.get('res_id', '')}"/>
        %endif
    </td>
</%def>


<%def name="render_float_line(line, date_range)">
    <tr id="${'line_%s' % line['id']}">
        ${render_resource(line)}
        <td>
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
        <td class="total">
            <%
                row_total = sum([v for (k, v) in line.get('cells_data', dict()).items()])
            %>
            <span id="row_total_${line['id']}"
                %if not editable and row_total <= 0.0:
                    class="zero"
                %endif
                >
                ${render_float(row_total)}
            </span>
        </td>
    </tr>
</%def>


<%def name="render_resource_list(resource_list)">
    %if len(resource_list) and editable:
        <select id="resource_list" kind="char" name="resource_list" type2="" operator="=" class="selection_search selection">
            <option value="default" selected="selected">&mdash; Select here new line's resource &mdash;</option>
            %for res in resource_list:
                <option value="${res[0]}">${res[1]}</option>
            %endfor
        </select>
        <span id="matrix_add_row" class="button">
            Add new line
        </span>
    %endif
</%def>


<div class="matrix ${' '.join(value.get('class', []))}">

    %if type(value) == type({}) and 'date_range' in value:

        <%
            lines = value.get('matrix_data', [])
            column_date_label_format = value.get('column_date_label_format', '%Y-%m-%d')
        %>

        %if editable:
            <div class="toolbar">
                ${render_resource_list(value.get('resource_list', []))}
                <span id="matrix_button_template" class="button increment">
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
                        <td>
                            <%
                                column_values = [line['cells_data'][date] for line in lines if line['widget'] != 'boolean' and date in line['cells_data']]
                            %>
                            %if len(column_values):
                                <%
                                    column_total = sum(column_values)
                                %>
                                <span id="column_total_${date}" class="
                                    %if not editable and column_total <= 0.0:
                                        zero
                                    %endif
                                    %if column_total > 1:
                                        warning
                                    %endif
                                    ">
                                        ${render_float(column_total)}
                                </span>
                            %endif
                        </td>
                    %endfor
                    <td>
                        <%
                            grand_total = sum([sum([v for (k, v) in line['cells_data'].items()]) for line in lines if line['widget'] != 'boolean'])
                        %>
                        <span id="grand_total"
                            %if not editable and grand_total <= 0.0:
                                class="zero"
                            %endif
                            >
                            ${render_float(grand_total)}
                        </span>
                    </td>
                </tr>
                %for line in [l for l in lines if l['widget'] == 'boolean']:
                    <tr id="${'line_%s' % line['id']}" class="boolean_line">
                        ${render_resource(line)}
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
                        <td class="total">
                            <%
                                row_total = sum([v for (k, v) in line.get('cells_data', dict()).items()])
                            %>
                            <span id="row_total_${line['id']}"
                                %if not editable and row_total <= 0.0:
                                    class="zero"
                                %endif
                                >
                                ${render_float(row_total)}
                            </span>
                        </td>
                    </tr>
                %endfor
            </tfoot>
            <tbody>
                <%
                    template_line = [l for l in lines if l['id'] == 'template'][0]
                    non_boolean_lines = [l for l in lines if l['id'] != 'template' and l['widget'] != 'boolean']
                    ungroupable_lines = [l for l in non_boolean_lines if 'group' not in l]
                    groups = list(set([l['group'] for l in lines if 'group' in l]))
                    date_range = value['date_range']
                %>
                %for line in ungroupable_lines:
                    ${render_float_line(line, date_range)}
                %endfor
                %for group in groups:
                    <tr id="${'group_%s' % group[0]}">
                        <td>
                            ${group[1]}
                        </td>
                        <td colspan="${len(date_range) + 2}">
                            ${render_resource_list(value.get('resource_list', []))}
                        </td>
                    </tr>
                    %for line in [l for l in non_boolean_lines if 'group' in l and l['group'][0] == group[0]]:
                        ${render_float_line(line, value['date_range'])}
                    %endfor
                %endfor
                ${render_float_line(template_line, value['date_range'])}
            </tbody>
        </table>

    %else:

        Can't render the matrix widget, unless a period is selected.

    %endif

</div>