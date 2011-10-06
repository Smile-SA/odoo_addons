<%
    import datetime
%>

<style type="text/css">
    .matrix table {
        border-spacing: .1em;
    }
    .matrix table input {
        width: 2em;
        min-width: 2em;
        border: 0;
    }
    .matrix table tbody td,
    .matrix table th,
    .matrix table tfoot tr.boolean_line td {
        border-style: dotted;
        border-color: #999;
        padding: .2em;
    }
    .matrix table tbody td,
    .matrix table th {
        border-width: 0 0 1px;
    }
    .matrix table tfoot tr.boolean_line td {
        border-width: 1px 0 0;
        font-weight: normal;
    }
    .matrix table tfoot span,
    .matrix table tbody span {
        float: right;
        text-align: right;
    }

    .matrix table .button.increment {
        display: block;
        width: 1.5em;
        text-align: center;
    }

    /*.wrapper.action-buttons {
        display:none;
    }*/
</style>

<div class="matrix">

    <span id="button_template" class="button increment">
        Button template
    </span>

    <table id="${name}">
        <thead>
            <tr>
                <th>Line</th>
                %for date in value['date_range']:
                    <th>${datetime.datetime.strptime(date, '%Y%m%d').strftime('%d/%m')}</th>
                %endfor
                <th>Total</th>
            </tr>
        </thead>
        <tfoot>
            <tr class="total_line">
                <td>Total</td>
                %for date in value['date_range']:
                    <td><span class="column_total_${date}"></span></td>
                %endfor
                <td><span id="grand_total"></span></td>
            </tr>
            %for line in [l for l in value.get('matrix_data', []) if l['type'] == 'boolean']:
                <tr class="boolean_line">
                    <td>${line['name']}</td>
                    %for date in value['date_range']:
                        <td class="boolean">
                            <%
                                cell_id = 'cell_%s_%s' % (line['id'], date)
                                cell_value = line['cells_data'].get(date, None)
                            %>
                            <input type="checkbox" name="${cell_id}" id="${cell_id}" kind="boolean" class="checkbox" readonly="readonly" disabled="disabled" value="${cell_value}">
<!--                            <br/>
                            <span kind="boolean" id="${cell_id}" value="${cell_value}">${cell_value}</span>-->
                        </td>
                    %endfor
                    <td></td>
                </tr>
            %endfor
        </tfoot>
        <tbody>
            %for line in [l for l in value.get('matrix_data', []) if l['type'] != 'boolean']:
                <tr>
                    <td>${line['name']}</td>
                    %for date in value['date_range']:
                        <td class="float">
                            <%
                                cell_id = 'cell_%s_%s' % (line['id'], date)
                                cell_value = line['cells_data'].get(date, None)
                            %>
                            <input type="text" kind="float" name="${cell_id}" id="${cell_id}" value="${cell_value}" size="1" class="float">
<!--                            <br/>
                            <span kind="float" id="${cell_id}" value="${cell_value}">${cell_value}</span>-->
                        </td>
                    %endfor
                    <td><span class="row_total_${line['id']}"></span></td>
                </tr>
            %endfor
        </tbody>
    </table>

</div>