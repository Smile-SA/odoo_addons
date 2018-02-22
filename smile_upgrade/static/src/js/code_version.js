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
                model: 'ir.code_version',
                method:'get_value',
            }).then(function(code_version) {
                self.$('.code_version').html(code_version);
            });
            return self._super();
        }
    });

    SystrayMenu.Items.push(DisplayCodeVersion);

});
