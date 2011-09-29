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
import netsvc

try:
    from mako.template import Template as MakoTemplate
except ImportError:
    netsvc.Logger().notifyChannel(_("Label"), netsvc.LOG_ERROR, _("Mako templates not installed"))

from osv import osv, fields


def year_month_tuples(year, month, max_year, max_month):
    # inspired by http://stackoverflow.com/questions/6576187/get-year-month-for-the-last-x-months
    _year, _month, _max_year, _max_month = year, month, max_year, max_month
    if max_year < year or (year==max_year and max_month < month):
        raise StopIteration
    while True:
        yield (_year, _month) # +1 to reflect 1-indexing
        _month += 1 # next time we want the next month
        if (_year==_max_year and _month>_max_month):
            raise StopIteration
        if _month == 13:
            _month = 1
            _year += 1


class smile_matrix(osv.osv_memory):
    _name = 'smile.matrix'

    _columns = {
        'name': fields.char("Name", size=32),
        }

    def _get_project(self, cr, uid, context):
        project_id = context and context.get('project_id',False)
        if project_id:
            return self.pool.get('smile.project').browse(cr, uid, project_id, context)
        return False

    def _get_project_months(self, project):
        start = datetime.datetime.strptime(project.start_date, '%Y-%m-%d')
        end = datetime.datetime.strptime(project.end_date, '%Y-%m-%d')
        return list(year_month_tuples(start.year, start.month, end.year, end.month))

    def fields_get(self, cr, uid, allfields=None, context=None, write_access=True):
        result = super(smile_matrix, self).fields_get(cr, uid, allfields, context, write_access)
        project = self._get_project(cr, uid, context)
        if project:
            for line in project.line_ids:
                for month in self._get_project_months(project):
                    month_str = self._month_to_str(month)
                    result['line_%s_%s' % (line.id, month_str)] = {'string': month_str, 'type':'integer', 'required':True, 'readonly': False}
        return result

    def _month_to_str(self, month):
        year = month[0]
        month = str(month[1]).zfill(2)
        return "%s_%s" % (year,month)

    mako_template = """
        <form string="Test">
            <html>
                <style type="text/css">
                    table#smile_matrix input {
                        width: 2em;
                        border: 0;
                    }
                    table#smile_matrix tfoot span,
                    table#smile_matrix input {
                        float: right;
                        text-align: right;
                    }
                    table#smile_matrix tbody td,
                    table#smile_matrix th {
                        border-bottom: 1px dotted #999;
                        padding: .2em;
                    }

                    table#smile_matrix .button.increment {
                        /* TODO Why this is not working ??? */
                        width: 2em;
                    }

                    .wrapper.action-buttons {
                        diplay:none;
                    }

                </style>
                <script type="application/javascript">
                    $(document).ready(function(){
                        $("input[name^='line_']").change(function(){
                            name_fragments = $(this).attr("id").split("_");
                            column_index = name_fragments[2] + '_' + name_fragments[3];
                            row_index = name_fragments[1];
                            // Select all fields of the columns we clicked in
                            var column_sum = 0;
                            $("input[name^='line_'][name$='_" + column_index + "']").each(function(){
                                column_sum += parseFloat($(this).val());
                            });
                            $("tfoot span.column_sum_" + column_index).text(column_sum);
                        });
                        $("tbody tr:first input[name^='line_']").trigger('change');

                        // Replace all integer fields by a button template, then hide the original field
                        var button_template = $("#button_template");
                        var cells = $("input[name^='line_']");
                        cells.each(function(i, cell){
                            var $cell = $(cell);
                            $cell.after($(button_template).clone().addClass($cell.attr("id")));
                            $cell.hide();
                        });
                        // Hide the button template
                        $(button_template).hide();

                        // Cycles buttons
                        var cycling_values = ['0', '0.5', '1'];
                        var buttons = $('.button.increment:not(.disabled)');
                        buttons.click(function(){
                            var button_value_tag = $(this).parent().find('input');
                            var button_label_tag = $(this);
                            var current_index = $.inArray(button_value_tag.val(), cycling_values);
                            var new_index = 0;
                            if(!isNaN(current_index)) {
                                new_index = (current_index + 1) % cycling_values.length;
                            };
                            var new_value = cycling_values[new_index];
                            button_label_tag.text(new_value);
                            button_value_tag.val(new_value);
                            button_value_tag.trigger('change');
                        });
                        buttons.trigger('click');

                    });
                </script>
                <span id="button_template" class="button increment">
                    Button template
                </span>
                <table id="smile_matrix">
                    <thead>
                        <tr>
                            <th>Line</th>
                            %for month in months:
                                <th>${"%s/%s" % (month[5:],month[2:4])}</th>
                            %endfor
                        </tr>
                    </thead>
                    <tfoot>
                        <tr>
                            <td>Sums:</td>
                            %for month in months:
                                <td><span class="column_sum_${month}">NaN</span></td>
                            %endfor
                        </tr>
                    </tfoot>
                    <tbody>
                        %for line in lines:
                            <tr>
                                <td>${line.name}</td>
                                %for month in months:
                                    <td>
                                        <field name="${'line_%s_%s' % (line.id, month)}"/>
                                    </td>
                                %endfor
                            </tr>
                        %endfor
                    </tbody>
                </table>
                <button string="Ok" name="validate" type="object"/>
            </html>
            <button string="Truc" name="machin" type="object"/>
        </form>
        """

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        project = self._get_project(cr, uid, context)
        if not project:
            return super(smile_matrix, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar, submenu)
        fields = self.fields_get(cr, uid, context=context)
        months = [self._month_to_str(month) for month in self._get_project_months(project)]
        arch = MakoTemplate(self.mako_template).render_unicode(months=months, lines=project.line_ids,
                                                         format_exceptions=True)
        return {'fields': fields, 'arch': arch}

    def validate(self, cr, uid, ids, context=None):
        if len(ids) != 1:
            raise osv.except_osv('Error', 'len(ids) !=1')
        print self.read(cr, uid, ids[0])
        return {'type': 'ir.actions.act_window_close'}

    def machin(self, cr, uid, ids, context=None):
        return True

    def create(self, cr, uid, vals, context=None):
        proj_fields = self.fields_get(cr, uid, context=context)
        today = datetime.datetime.today()
        for f in proj_fields:
            if f not in self._columns:
                if proj_fields[f]['type'] == 'integer':
                    self._columns[f] = fields.integer(create_date=today, **proj_fields[f])
            elif hasattr(self._columns[f], 'create_date'):
                self._columns[f].create_date = today
        return super(smile_matrix, self).create(cr, uid, vals, context)

    def vaccum(self, cr, uid, force=False):
        super(smile_matrix, self).vaccum(cr, uid, force)
        today = datetime.datetime.today()
        fields_to_clean = []
        for f in self._columns:
            if hasattr(self._columns[f], 'create_date') and (self._columns[f].create_date < today  - datetime.timedelta(days=1)):
                unused = True
                for val in self.datas.values():
                    if f in val:
                        unused=False
                        break
                if unused:
                    fields_to_clean.append(f)
        for f in fields_to_clean:
            del self._columns[f]
        return True

smile_matrix()
