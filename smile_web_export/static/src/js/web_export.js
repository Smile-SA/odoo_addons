openerp.smile_web_export = function(instance) {

    var _t = instance.web._t;

    instance.web.Sidebar.include({

        add_items: function(section_code, items) {
            var self = this,
                _sup = _.bind(this._super, this),
                model = this.session.model('res.users'),
                args = ['smile_web_export.group_export'];
            model.call('has_group', args).then(function(can_export) {
                if (can_export) {
                    _sup.call(self, section_code, items);
                } else {
                    var export_label = _t("Export"),
                        new_items = items;
                    if (section_code == 'other') {
                        new_items = [];
                        for (var i = 0; i < items.length; i++) {
                            if (items[i]['label'] != export_label) {
                                new_items.push(items[i]);
                            };
                        };
                    };
                    _sup.call(self, section_code, new_items);
                }
            });
        }

    });

};
