
odoo.define('smile_many2many_tags_clickable.form_relational', function (require) {
    "use strict";
//
    var core = require('web.core');
    var fieldRegistry = require('web.field_registry');
    var FormFieldMany2ManyTags = fieldRegistry.get('form.many2many_tags');
    var Dialog = require('web.view_dialogs');
    var _t = core._t;

//
    FormFieldMany2ManyTags.include({

        _onOpenColorPicker: function (ev){
            if (this.mode === "readonly") {
                new Dialog.FormViewDialog(this, {
                    res_model: this.value.model,
                    res_id: $(ev.currentTarget).data('id'),
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
