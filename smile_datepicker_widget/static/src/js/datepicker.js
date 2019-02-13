/*
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define('smile_datepicker_widget.datepicker', function (require) {
    "use strict";
    var Widget = require('web.datepicker');

    /**
     * Adds 'datepicker_start_date' and 'datepicker_step' (default: 1) in options
     * of widgets Date and Datetime.
     * If option 'datepicker_start_date' is set, then the default value set
     * for the field will be the value of the field designed by option
     * 'datepicker_start_date' + 1 day.
     */
    Widget.DateWidget.include({
        _onShow: function (e) {
            e.preventDefault();
            var parent = this.getParent();
            if (typeof parent !== 'undefined' && typeof parent.field !== 'undefined' && (parent.field.type === 'date' ||
                parent.field.type === 'datetime') && parent.nodeOptions.datepicker_start_date !== 'undefined') {
                debugger;
                var fields = this.__parentedParent.__parentedParent.allFieldWidgets;
                var arr = Object.values(fields);
                var start_field_name = parent.nodeOptions.datepicker_start_date;
                var step = 1;
                if (parent.nodeOptions.datepicker_step !== 'undefined'
                    && typeof (parent.nodeOptions.datepicker_step) == 'number') {
                    step = parent.nodeOptions.datepicker_step;
                }
                for (var i in arr[0]) {
                    if (arr[0][i].name == start_field_name) {
                        if (moment.isMoment(arr[0][i].value)) {
                            var end_day = arr[0][i].value.clone();
                            end_day.add(step, 'd');
                            this.picker.date(end_day);
                            this.picker.viewDate(end_day);
                            if (this.$input.val().length !== 0 && this.isValid()) {
                                var value = this._parseClient(this.$input.val());
                                this.picker.date(value);
                                this.$input.select();
                            }
                        }
                    }
                }
            }
        },
    });
});
