odoo.define('display_code_version', function (require) {
    'use strict';

    const rpc = require('web.rpc');
    const SystrayMenu = require('web.SystrayMenu');
    const Widget = require('web.Widget');
    const { Component, useState } = owl;

    class DisplayCodeVersion extends Component {
        setup () {
            let self = this;
            self.state = useState({
                code_version: "",
            })
            rpc.query({
                model: 'ir.code_version',
                method:'get_value',
            }).then(function(response) {
                return response;
            }).then(function(data) {
                Object.assign(self.state, {code_version: data,});
            });
        }
    }
    DisplayCodeVersion.template = "smile_upgrade.DisplayCodeVersion";
    SystrayMenu.Items.push(DisplayCodeVersion);

});
