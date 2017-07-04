odoo.define('smile_widgets_extension.form_relational', function (require) {
    "use strict";

    var core = require('web.core');
    var FieldMany2ManyTags = core.form_widget_registry.get('many2many_tags');
    var common = require('web.form_common');
    var _t = core._t;

    FieldMany2ManyTags.include({
        open_color_picker: function(ev){
            if (this.view.get("actual_mode") === "view") {
                new common.FormViewDialog(this, {
                    res_model: this.dataset.model,
                    res_id: $(ev.currentTarget).data('id'),
                    title: _t("Open: ") + this.string,
                    views: [[false, 'form']],
                    readonly: this.options.no_edit || this.options.no_create_edit,
                }).open();
            } else {
                this._super(ev);
            }
        },
    });

});
