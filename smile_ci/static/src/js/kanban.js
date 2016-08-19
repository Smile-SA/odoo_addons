odoo.define('smile_ci.Dashboard', function (require) {
    'use strict';

    var KanbanView = require('web_kanban.KanbanView');
    var KanbanColumn = require('web_kanban.Column');
    var KanbanRecord = require('web_kanban.Record');
    var session = require('web.session');

    KanbanView.include({
        render: function () {
            this._super();
            if (this.model == 'scm.repository.branch.build' && this.default_group_by == 'branch_id') {
                this.$el.find('.o_kanban_config').hide();
                _.each(this.$el.find('.o_column_button'), function (node) {
                    $(node).show();
                });
                this.manage_subcription_buttons_visibility();
            }
        },
        manage_subcription_buttons_visibility: function () {
            var self = this,
                model = 'scm.repository.branch',
                method = 'read',
                branch_ids = _.map(this.data['groups'], function (group) {return group['id']}),
                fields = ['message_is_follower'];
            this.rpc('/web/dataset/call_kw/' + model + '/' + method,  {
                model: model,
                method: method,
                args: [branch_ids, fields],
                kwargs: {},
            }, []).then(function (branch_infos) {
                _.each(self.$el.children(), function (node) {
                    var $node = $(node);
                    var node_id = parseInt($node.attr('data-id'));
                    var is_follower = _.findWhere(branch_infos, {id: node_id})['message_is_follower'];
                    var buttons = [{id: 'a.o_branch_subcribe', follow: true}, {id: 'a.o_branch_unsubcribe', follow: false}];
                    _.each(buttons, function (button) {
                        var $subnode = $node.find(button['id']);
                        if ($subnode) {
                            if (is_follower == button['follow']) {
                                $subnode.hide();
                            } else {
                                $subnode.show();
                            }
                        }
                    });
                });
            });
        },
    });

    KanbanColumn.include({
        events: _.extend(KanbanColumn.prototype.events, {
            'click .o_branch_test': 'launch_branch_test',
            'click .o_branch_force_test': 'launch_branch_force_test',
            'click .o_branch_subcribe': 'launch_branch_subcribe',
            'click .o_branch_unsubcribe': 'launch_branch_unsubcribe',
        }),
        launch_branch_method: function (event, method, kwargs) {
            event.preventDefault();
            var self = this,
                model = 'scm.repository.branch';
            this.rpc('/web/dataset/call_kw/' + model + '/' + method,  {
                model: model,
                method: method,
                args: [this.id],
                kwargs: {},
            }, []).then(function (result) {
                self.trigger_up('kanban_reload');
            });
        },
        launch_branch_test: function (event) {
            this.launch_branch_method(event, 'create_build', {});
        },
        launch_branch_force_test: function (event) {
            this.launch_branch_method(event, 'force_create_build', {});
        },
        launch_branch_subcribe: function (event) {
            this.launch_branch_method(event, 'message_subscribe_users', {'user_ids': [session.uid]});
        },
        launch_branch_unsubcribe: function (event) {
            this.launch_branch_method(event, 'message_unsubscribe_users', {'user_ids': [session.uid]});
        },
    });

    KanbanRecord.include({
        kanban_coverage_level: function(percent) {
            return parseInt(percent / 25);
        },
    });

});
