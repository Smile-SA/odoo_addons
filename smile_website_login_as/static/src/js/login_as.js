odoo.define('login_as', function (require) {
    'use strict';

    var core = require('web.core');
    var session = require('web.session');
    var Model = require('web.DataModel');
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    var _t = core._t;

    var LoginAs = Widget.extend({
        template: 'LoginAs',
        events: {
            'click a#login_as': 'login_as',
        },
        login_as: function() {
            var self = this;
            new Model('ir.ui.view').call('get_view_id', ['smile_website_login_as.view_res_users_login_as_form']).then(function (view_id) {
                self.do_action({
                    type: 'ir.actions.act_window',
                    name: _t('Login as'),
                    views: [[view_id, 'form']],
                    res_model: 'res.users',
                    res_id: session.uid,
                    target: 'new',
                });
            });
        }
    });

    SystrayMenu.Items.push(LoginAs);

});
