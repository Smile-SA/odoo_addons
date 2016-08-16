odoo.define('add_environment_ribbon', function (require) {
    'use strict';

    var Model = require('web.DataModel');
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');

    var EnvironmentRibbon = Widget.extend({
        template: 'EnvironmentRibbon',
        start: function() {
            var self = this,
                config_parameter = new Model('ir.config_parameter');
            config_parameter.call('get_param', ['server.environment', 'prod']).then(function(server_env) {
                self.$el.html(server_env.toUpperCase());
            });
            config_parameter.call('get_param', ['server.environment.ribbon_color', 'rgba(255, 0, 0, .6)']).then(function(color) {
                self.$el.css({'background-color': color});
            });
            return self._super();
        }
    });

    var config_parameter = new Model('ir.config_parameter');
    config_parameter.call('get_param', ['server.environment', 'prod']).then(function(server_env) {
        if (server_env != 'prod') {
            SystrayMenu.Items.push(EnvironmentRibbon);
        }
    });

});
