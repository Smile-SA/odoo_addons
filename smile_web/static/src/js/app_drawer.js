odoo.define('smile_web.app_drawer', function (require) {
    "use strict";

    var web_responsive = require('web_responsive');
    var rpc = require('web.rpc');
    var session = require('web.session');

    function clean_string(str) {
        return str.toLowerCase().normalize(
            'NFD').replace(/[\u0300-\u036f]/g, "");
    };

    web_responsive.AppDrawer.include({

        /**
         * Open Drawer at login
         */ 
        init: function () {
            this._super();
            $('.drawer').drawer('open');
            this._getMenus();
        },

        /**
         * Search in complete_name instead of name
         */
        _getMenus: function () {
            var self = this;
            rpc.query({
                model: 'ir.ui.menu',
                method: 'search_read',
                kwargs: {
                    fields: ['action', 'display_name', 'id'],
                    domain: [
                        '|',
                        ['action', '!=', false],
                        ['parent_id', '=', false],
                    ],
                    context: session.user_context,
                },
            }).then( function (menus) {
                self.menus = menus;
            });
        },
         _searchMenus: function () {
            var self = this;
            var found_menus = _.filter(this.menus, function(menu) {
                return clean_string(menu.display_name).indexOf(
                    clean_string(self.$searchInput.val())) !== -1;
            });
            this.showFoundMenus(found_menus);
        },
        showFoundMenus: function(menus) {
            menus.sort(function(a, b) {
                return a.display_name.localeCompare(b.display_name);
            });
            this._super.apply(this, arguments)
        },
    });

});
