odoo.define('translate_progress_bar_title', function (require) {
    'use strict';

    var core = require('web.core');
    var ProgressBar = require('web.ProgressBar');
    var _t = core._t;

    ProgressBar.include({
        init: function (parent, options) {
            this._super(parent, options);
            this.title = _t(options.title);
        },
    });

});
