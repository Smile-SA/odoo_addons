odoo.define('web_import', function (require) {
    "use strict";

    var ListView = require('web.ListView');
    var Model = require('web.DataModel');

    ListView.include({

        render_buttons: function($node) {
            this._super.apply(this, arguments);
            var model = new Model('res.users'),
                self = this,
                args = ['smile_web_import.group_import'];
            model.call('has_group', args).then(function(can_import) {
                if (!can_import) {
                    self.$buttons.find('.o_list_button_import').hide();
                }
            });
        },

    });

});
