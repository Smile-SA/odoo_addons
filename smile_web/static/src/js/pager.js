odoo.define('smile_web.pager', function (require) {
    "use strict";

    var Pager = require('web.Pager');
    var rpc = require('web.rpc');
    var utils = require('web.utils');

    Pager.include({

        /**
         * Limit the pager range to value defined in parameter "pager.limit"
         */
        _save: function ($input) {
            var self = this;
            this.options.validate().then(function() {
                var value = $input.val().split("-");
                var min = utils.confine(parseInt(value[0], 10), 1, self.state.size);
                var max = utils.confine(parseInt(value[1], 10), 1, self.state.size);
                rpc.query({
                    model: 'ir.pager_limit',
                    method: 'get_value',
                }).then(function(pager_limit) {
                    max = Math.min(min + pager_limit - 1, max);
                    if (!isNaN(min)) {
                        self.state.current_min = min;
                        if (!isNaN(max)) {
                            self.state.limit = utils.confine(max-min+1, 1, self.state.size);
                        } else {
                            // The state has been given as a single value -> set the limit to 1
                            self.state.limit = 1;
                        }
                        self.trigger('pager_changed', _.clone(self.state));
                    }
                });
            }).always(function() {
                // Render the pager's new state (removes the input)
                self._render();
            });
        },
    });

});
