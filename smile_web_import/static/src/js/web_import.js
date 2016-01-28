openerp.smile_web_import = function(instance) {

    var _t = instance.web._t;

    instance.web.ListView.include({

        load_list: function () {
            var model = this.session.model('res.users'),
                args = ['smile_web_import.group_import'],
                elem = this.__parentedParent.$el,
                result = this._super.apply(this, arguments);
            model.call('has_group', args).then(function(can_import) {
                if (!can_import) {
                    elem.find('.oe_list_button_import').hide();
                    elem.find('.oe_fade').hide();
                }
            });
            return result;
        },
        start_edition: function (record, options) {
            this._super.apply(this, arguments);
            $('.oe_fade').show();
        },
        save_edition: function () {
            $('.oe_fade').hide();
            return this._super.apply(this, arguments);
        },
        cancel_edition: function (force) {
            $('.oe_fade').hide();
            return this._super.apply(this, arguments);
        }
    });

};
