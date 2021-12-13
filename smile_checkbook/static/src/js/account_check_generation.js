odoo.define('smile_checkbook.account_check_generation', function (require) {
    "use strict";

    var core = require('web.core');
    var ListController = require('web.ListController');
    var _t = core._t;

    function account_check_generator () {
        var action = {
            type: 'ir.actions.act_window',
            name: _t('Account Check Generator'),
            res_model: 'account.checkbook.wizard',
            views: [[false, 'form']],
            target: 'new',
        };
        this.do_action(action);
    }

    ListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            if (this.modelName === 'account.check') {
                this.$buttons.off('click', '.o_list_button_add')
                this.$buttons.on('click', '.o_list_button_add', account_check_generator.bind(this));
                var button_add = this.$buttons.find('.btn.btn-primary.btn-sm.o_list_button_add');
                if (button_add && button_add[0]) {
                    button_add[0].innerHTML = _t('Generate checks')
                }
            }
        },
    });
});
