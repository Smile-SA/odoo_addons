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
                model: 'ir.config_parameter',
                method: 'get_param',
                args: ['server.environment', 'prod'],
            }).then(function(server_env) {
                self.$el.html(server_env.toUpperCase());
            });
            config_parameter.call('get_param', ['server.environment.ribbon_color', 'rgba(255, 0, 0, .6)']).then(function(color) {
                self.$el.css({'background-color': color});
            });
            return self._super();
        }
    });

    rpc.query({
        model: 'ir.config_parameter',
        method: 'get_param',
        args: ['server.environment', 'prod'],
    }).then(function(server_env) {
        if (server_env != 'prod') {
            SystrayMenu.Items.push(EnvironmentRibbon);
        }
    });

});
