odoo.define('add_environment_ribbon', function (require) {
    'use strict';

    var core = require('web.core');
    var Model = require('web.DataModel');
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');

    var EnvironmentRibbon = Widget.extend({
        init: function(parent) {
            var self = this,
                config_parameter = new Model('ir.config_parameter');
            config_parameter.call('get_param', ['server.environment', 'prod']).then(function(server_env) {
                self.$el.append('<div class="environment_ribbon">' + server_env.toUpperCase() + '</div>')
            });
            config_parameter.call('get_param', ['server.environment.ribbon_color', 'rgba(255, 0, 0, .6)']).then(function(color) {
                $(".environment_ribbon").css({'background-color': color});
            });
            self._super(parent);
        }
    });

    var config_parameter = new Model('ir.config_parameter');
    config_parameter.call('get_param', ['server.environment', 'prod']).then(function(server_env) {
        if (server_env != 'prod') {
            SystrayMenu.Items.push(EnvironmentRibbon);
        }    
    });

});
