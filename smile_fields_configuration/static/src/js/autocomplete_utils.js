odoo.define('smile_fields_configuration.autocomplete_utils', function (require) {
'use strict';

    var fieldUtils = require('web.field_utils');
    var pyUtils = require("web.py_utils");

    function transformRecord(record, recordData) {
        var newRecord = {};
        _.each(record.getFieldNames(), function (name) {
            var value = recordData[name];
            var r = _.clone(record.fields[name] || {});
            if ((r.type === 'date' || r.type === 'datetime') && value) {
                var dateFormat = r.type === 'datetime' ? 'YYYY-MM-DD HH:mm:ss' : 'YYYY-MM-DD';
                r.raw_value = moment(value).format(dateFormat);
            } else if (r.type === 'one2many' || r.type === 'many2many') {
                r.raw_value = value.count ? value.res_ids : [];
            } else if (r.type === 'many2one') {
                r.raw_value = value && value.res_id || false;
            } else {
                r.raw_value = value;
            }
            newRecord[name] = r.raw_value;
        });
        return newRecord;
    }

    function selectedItem(self, item) {
        self._rpc({
            model: 'ir.referencial',
            method: 'convert_fields_referencial',
            args: [item, self.referencialId, transformRecord(self.record, self.recordData), self.model],
        }).then(function (result) {
            var values = result[0];
            var errors = result[1];
            var action_redirect = result[2];
            if (values) {
                self.trigger_up('field_changed', {
                    dataPointID: self.dataPointID,
                    changes: values,
                });
            }
            self.$el.val('');
            if (action_redirect) {
                const context = pyUtils.py_eval(action_redirect.context);
                context.form_view_initial_mode = 'edit';
                action_redirect.context = context;
                self.do_action(action_redirect);
            } else if (errors.length) {
                self._rpc({
                    model: 'ir.referencial',
                    method: 'open_wizard_warning_error',
                    args: [errors],
                }).then(function (action) {
                    self.do_action(action);
                });
            }
        });
    }

    return {
        transformRecord: transformRecord,
        selectedItem: selectedItem,
    };

});
