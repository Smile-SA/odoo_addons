odoo.define('add_environment_ribbon', function (require) {
    'use strict';

    var rpc = require('web.rpc');
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');

    var EnvironmentRibbon = Widget.extend({
        template: 'EnvironmentRibbon',
        start: function() {
            var self = this;
            rpc.query({
                model: 'ir.env_ribbon',
                method: 'get_values',
            }).then(function(env_ribbon) {
                self.$el.html(env_ribbon[0].toUpperCase());
                self.$el.css({'background-color': env_ribbon[1]});
            });
            return self._super();
        }
    });

    rpc.query({
        model: 'ir.env_ribbon',
        method: 'get_values',
    }).then(function(env_ribbon) {
        if (env_ribbon[0] != 'prod') {
            SystrayMenu.Items.push(EnvironmentRibbon);
        }
    });

});
