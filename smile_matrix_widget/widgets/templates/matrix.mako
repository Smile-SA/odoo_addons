<%
    import datetime
%>

<style type="text/css">
    .matrix .toolbar {
        margin-bottom: 1em;
    }

    .matrix table {
        text-align: center;
        margin-bottom: 1em;
    }

    .matrix td,
    .matrix th {
        min-width: 1.5em;
        height: 1.5em;
    }

    .non-editable .matrix td,
    .non-editable .matrix th {
        padding: 0 .4em;
    }

    .matrix table .button {
        padding-left: .3em;
        padding-right: .3em;
    }

    .matrix table .button.increment {
        width: 1.5em;
        height: 1.5em;
        line-height: inherit;
    }

    .matrix .zero {
        color: #ccc;
    }

    .matrix table thead th {
        text-transform: none;
    }

    .matrix table .first_column {
        text-align: left;
    }

    .matrix table .total {
        font-weight: bold;
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
        font-weight: normal;
    }

    .matrix table tfoot span,
    .matrix table tbody span {
        display: block;
    }

    .matrix table tfoot input {
        width: none;
    }
</style>


<%def name="render_float(f)">
    %if int(f) == f:
        ${int(f)}
    %else:
        ${f}
    %endif
</%def>


<div class="matrix">

    %if type(value) == type({}) and 'date_range' in value:

        <%
            lines = value.get('matrix_data', [])
        %>

        %if editable:
            <div class="toolbar">
                <span id="matrix_add_row" class="button">
                    Add line
                </span>
                <span id="matrix_button_template" class="button increment">
                    Button template
                </span>
            </div>
        %endif

        <table id="${name}">
            <thead>
                <tr>
                    <th class="first_column">Line</th>
                    <th></th>
                    %for date in value['date_range']:
                        <th>${datetime.datetime.strptime(date, '%Y%m%d').strftime('%d')}</th>
                    %endfor
                    <th class="total">Total</th>
                </tr>
            </thead>
            <tfoot>
                <tr class="total_line">
                    <td class="first_column">Total</td>
                    <td></td>
                    %for date in value['date_range']:
                        <td>
                            <%
                                column_values = [line['cells_data'][date] for line in lines if line['type'] == 'float' and date in line['cells_data']]
                            %>
                            %if len(column_values):
                                <%
                                    column_total = sum(column_values)
                                %>
                                <span id="column_total_${date}"
                                    %if not editable and column_total <= 0.0:
                                        class="zero"
                                    %endif
                                    >
                                        ${render_float(column_total)}
                                </span>
                            %endif
                        </td>
                    %endfor
                    <td class="total">
                        <%
                            grand_total = sum([sum([v for (k, v) in line['cells_data'].items()]) for line in lines if line['type'] == 'float'])
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
                %for line in [l for l in lines if l['type'] == 'boolean']:
                    <tr class="boolean_line">
                        <td class="first_column">${line['name']}</td>
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
                                        <input type="checkbox" enabled="enabled" kind="boolean" class="checkbox" id="${cell_id}"
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
                        <td class="total"></td>
                    </tr>
                %endfor
            </tfoot>
            <tbody>
                %for line in [l for l in lines if l['type'] != 'boolean']:
                    <tr>
                        <td class="first_column">${line['name']}</td>
                        <td>
                            %if editable:
                                <span class="button delete_row">X</span>
                            %endif
                        </td>
                        %for date in value['date_range']:
                            <td class="float">
                                <%
                                    cell_id = 'cell_%s_%s' % (line['id'], date)
                                    cell_value = line.get('cells_data', {}).get(date, None)
                                %>
                                %if cell_value is not None:
                                    %if editable:
                                        <input type="text" kind="float" name="${cell_id}" id="${cell_id}" value="${render_float(cell_value)}" size="1" class="float"/>
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
                %endfor
            </tbody>
        </table>

    %else:

        Can't render the matrix widget, unless a period is selected.

    %endif

</div>