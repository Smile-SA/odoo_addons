odoo.define('web_impex', function (require) {
    'use strict';

    var core = require("web.core");
    var Sidebar = require('web.Sidebar');
    var KanbanController = require('web.KanbanController');
    var ListController = require("web.ListController");
    var _t = core._t;

    KanbanController.include({
        /**
         * Hide "Import" button if user has no Import group.
         */
        renderButtons: function () {
             var self = this;
            this._super.apply(this, arguments); // Sets this.$buttons

            this.getSession().user_has_group('smile_web_impex.group_import').then(function(has_group) {
                if(!has_group) {
                    if (self.$buttons) {
                        self.$buttons.find('.o_button_import').hide();
                    }
                }
                else {
                    if (self.$buttons) {
                      self.$buttons.find('.o_button_import').show();
                    }
                }
            });
        },
    });


    ListController.include({
        /**
         * Hide "Import" button if user has no Import group.
         */
        renderButtons: function () {
            var self = this;
            this._super.apply(this, arguments); // Sets this.$buttons

            this.getSession().user_has_group('smile_web_impex.group_import').then(function(has_group) {
                if(!has_group) {
                    if (self.$buttons) {
                        self.$buttons.find('.o_button_import').hide();
                    }
                }
                else {
                    if (self.$buttons) {
                        self.$buttons.find('.o_button_import').show();
                    }
                }
            });

        },

         _updateButtons: function (mode) {
            var self = this;
            this._super.apply(this, arguments);
          this.getSession().user_has_group('smile_web_impex.group_export').then(function(has_group) {
                if(!has_group) {
                      self.$buttons.find('.o_list_export_xlsx').hide();
                }
                  else {
                      self.$buttons.find('.o_list_export_xlsx').show();
                }
            });
    },

        /**
         * Hide "Export" action if user has no Export group.
         */
        renderSidebar: async function ($node) {
            var self = this;
            if (this.hasSidebar && !this.sidebar) {
            var other = [];
            var has_export_group = false;

            const group_export = await this.getSession().user_has_group('smile_web_impex.group_export').then(function(has_group) {
                    if(has_group) {
                        has_export_group = true;
                    } else {
                        has_export_group = false;
                    }
                });

                if (has_export_group) {
                    other = [{
                        label: _t("Export"),
                        callback: this._onExportData.bind(this)
                    }];
                }
                  if (this.archiveEnabled) {
                    other.push({
                        label: _t("Archive"),
                        callback: this._toggleArchiveState.bind(this, true)
                    });

                    other.push({
                        label: _t("Unarchive"),
                        callback: this._toggleArchiveState.bind(this, false)
                    });
                }
                if (this.is_action_enabled('delete')) {
                    other.push({
                        label: _t('Delete'),
                        callback: this._onDeleteSelectedRecords.bind(this)
                    });
                }

             self.sidebar = new Sidebar(self, {
                    editable: self.is_action_enabled('edit'),
                    env: {
                        context: self.model.get(self.handle).getContext(),
                        activeIds: self.getSelectedIds(),
                        model: self.modelName,
                    },
                    actions: _.extend(self.toolbarActions, {other: other}),
                });

                  return self.sidebar.appendTo($node).then(function() {
                   self._toggleSidebar();
            });

            }
            return Promise.resolve();
        }
    });

});
