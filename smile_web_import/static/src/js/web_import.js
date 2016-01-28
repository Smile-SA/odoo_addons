openerp.smile_web_import = function(instance) {

    var _t = instance.web._t;

    instance.web.Sidebar.include({

        add_items: function(section_code, items) {
            var self = this,
                _sup = _.bind(this._super, this),
                Users = new instance.web.DataSet(self, 'res.users'),
                args = ['smile_web_import.group_import'];
            Users.call('has_group', args).then(function(can_import) {
                if (can_import) {
                    _sup.call(self, section_code, items);
                } else {
                    var import_label = _t("Import"),
                        new_items = items;
                    if (section_code == 'other') {
                        new_items = [];
                        for (var i = 0; i < items.length; i++) {
                            if (items[i]['label'] != import_label) {
                                new_items.push(items[i]);
                            };
                        };
                    };
                    _sup.call(self, section_code, false);
                }
            });
        }

    });

};
