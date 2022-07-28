odoo.define('smile_customize_data.customizeView', function (require) {
'use strict';

    var core = require('web.core');
    var Widget = require('web.Widget');
    var Dialog = require('web.Dialog');
    var ActionManager = require('web.ActionManager');
    var FormController = require('web.FormController');
    var ListController = require('web.ListController');
    var qweb = core.qweb;

    var CustomizeView = Widget.extend({
        template: "CustomizeView",
        events: {
            "click a": "open_customize_view",
        },

        init: function (options) {
            this._super.apply(this, arguments);
            this.viewId = options.viewId || false;
            this.viewType = options.viewType || false;
            this.modelName = options.modelName || false;
        },

        open_customize_view: function (evt) {
            evt.preventDefault();
            var self = this;
            this._rpc({
                model: 'ir.ui.view',
                method: 'open_custom_view',
                args: [self.viewId, self.viewType, self.modelName],
            }).then(function (action) {
                self.do_action(action);
            });
        },
    });

    Dialog.include({
        open: function() {
            var self = this;
            this.opened(function() {
                setTimeout(function () {
                    var parent = self.getParent();
                    var noCustomize =  (self.context && self.context.no_customize) || (parent && parent.currentDialogController && parent.currentDialogController.widget && parent.currentDialogController.widget.initialState && parent.currentDialogController.widget.initialState.context.no_customize) || false;
                    var viewId = (self.form_view && self.form_view.viewId) || (parent && parent.currentDialogController && parent.currentDialogController.widget && parent.currentDialogController.widget.viewId) || false;
                    if (viewId && !noCustomize) {
                        self.getSession().user_has_group('smile_customize_data.data_manager').then(function(hasGroup) {
                            if (hasGroup) {
                                self.customizeView = new CustomizeView(self);
                                var $header = self.$modal.find('.modal-header:first');
                                return self.customizeView.prependTo($header).then(function () {
                                    self.customizeView.viewId = viewId;
                                });
                            }
                        });
                    }
                }, 0);
            });
            return this._super.apply(this, arguments);
        },
    });

    FormController.include({
        renderButtons: function ($node) {
            var self = this;
            this._super.apply(this, arguments);
            if (this.$buttons) {
                this.getSession().user_has_group('smile_customize_data.data_manager').then(function(hasGroup) {
                    if (hasGroup) {
                        var options = {
                            'viewId': self.viewId,
                            'viewType': self.viewType,
                            'modelName': self.modelName,
                        };
                        var $customizeButton = $(qweb.render('CustomizeViewButton'));
                        self.$buttons.find('.o_form_button_create').after($customizeButton);
                        self.$buttons.on('click', '.o_button_customize', new CustomizeView(options).open_customize_view.bind(self));
                    }
                });
            }
        },
    });

    ListController.include({
        renderButtons: function ($node) {
            var self = this;
            this._super.apply(this, arguments);
            if (this.$buttons) {
                this.getSession().user_has_group('smile_customize_data.data_manager').then(function(hasGroup) {
                    if (hasGroup) {
                        var options = {
                            'viewId': self.viewId,
                            'viewType': self.viewType,
                            'modelName': self.modelName,
                        };
                        var $customizeButton = $(qweb.render('CustomizeViewButton'));
                        self.$buttons.append($customizeButton);
                        self.$buttons.on('click', '.o_button_customize', new CustomizeView(options).open_customize_view.bind(self));
                    }
                });
            }
        },
    });

});
