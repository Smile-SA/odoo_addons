odoo.define('smile_many2many_tags_clickable.form_relational', function (require) {
    "use strict";

    var core = require('web.core');
    var dialogs = require('web.view_dialogs');
    var relational_fields = require('web.relational_fields');
    var FormFieldMany2ManyTags = relational_fields.FormFieldMany2ManyTags;
    var _t = core._t;

    FormFieldMany2ManyTags.include({
        _onOpenColorPicker: function (ev) {

        var tagID = $(ev.currentTarget).parent().data('id');
        var tag = _.findWhere(this.value.data, { res_id: tagID });
        var $this = $(ev.target);
        var self = this;

        if (this.mode === 'readonly') {
            ev.preventDefault();
            ev.stopPropagation();
           new dialogs.FormViewDialog(self, {
                res_model: tag.model,
                res_id: tag.data.id,
                title: _t("Open: ") + this.string,
                views: [[false, 'form']],
                readonly: this.nodeOptions.no_edit || this.nodeOptions.no_create_edit,
            }).open();
        } else {
            this._super(ev);
        }
    },
    });
});


