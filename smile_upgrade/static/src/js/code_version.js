odoo.define('display_code_version', function (require) {
    'use strict';

    var Model = require('web.DataModel');
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');

    var DisplayCodeVersion = Widget.extend({
        template: 'DisplayCodeVersion',
        start: function() {
            var self = this,
                config_parameter = new Model('ir.config_parameter');
            config_parameter.call('get_param', ['code.version', '?!']).then(function(code_version) {
                self.$('.code_version').html(code_version);
            });
            return self._super();
        }
    });

    SystrayMenu.Items.push(DisplayCodeVersion);

});
