odoo.define('display_code_version', function (require) {
    'use strict';

    var rpc = require('web.rpc');
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');

    var DisplayCodeVersion = Widget.extend({
        template: 'DisplayCodeVersion',
        start: function() {
            var self = this;
            rpc.query({
                model: 'ir.config_parameter',
                method:'get_param',
                args: ['code.version', '?!'],
            }).then(function(code_version) {
                self.$('.code_version').html(code_version);
            });
            return self._super();
        }
    });

    SystrayMenu.Items.push(DisplayCodeVersion);

});
