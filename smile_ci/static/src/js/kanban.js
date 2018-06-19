odoo.define('smile_ci.Dashboard', function (require) {
    'use strict';

    var KanbanView = require('web_kanban.KanbanView');
    var KanbanColumn = require('web_kanban.Column');
    var KanbanRecord = require('web_kanban.Record');
    var Model = require('web.Model');

    KanbanView.include({
        render: function () {
            this._super();
            if (this.model == 'scm.repository.branch.build' && this.group_by_field != undefined) {
                this.$el.find('.o_kanban_config').hide();
                _.each(this.$el.find('.o_column_button'), function (node) {
                    $(node).show();
                });
                this.manage_subcription_buttons_visibility();
            }
        },
        manage_subcription_buttons_visibility: function () {
            var self = this,
                branch_ids = _.map(this.data['groups'], function (group) {return group['id']}),
                fields = ['message_is_follower'];
            new Model('scm.repository.branch').call('read', [branch_ids, fields]).then(function (branch_infos) {
                _.each(self.$el.children(), function (node) {
                    var $node = $(node);
                    var node_id = parseInt($node.attr('data-id'));
                    var branch = _.findWhere(branch_infos, {id: node_id});
                    var is_follower = branch? branch['message_is_follower']: false;
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
        init: function(parent, group_data, options, record_options) {
            this._super(parent, group_data, options, record_options);
            this.group_on = group_data.attributes.grouped_on;
        },
        start: function() {
            this._super();
            if (this.group_on == 'branch_id' && this.dataset.model == 'scm.repository.branch.build') {
                this.$el.find('.o_column_title').css('cursor', 'pointer');
            }
        },
        events: _.extend(KanbanColumn.prototype.events, {
            'click .o_column_title': 'column_open_form',
            'click .o_branch_test': 'branch_test',
            'click .o_branch_force_test': 'branch_force_test',
            'click .o_branch_download_docker_image': 'branch_download_docker_image',
            'click .o_branch_subcribe': 'branch_subcribe',
            'click .o_branch_unsubcribe': 'branch_unsubcribe',
        }),
        column_open_form: function (event) {
            if (this.group_on == 'branch_id' && this.dataset.model == 'scm.repository.branch.build') {
                var self = this;
                new Model(this.dataset.model).call('fields_get', [this.group_on]).then(function (fields) {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: fields[self.group_on].relation,
                        res_id: self.id,
                        views: [[false, 'form']],
                        target: 'current',
                    });
                });
            }
        },
        call_branch_method: function (event, method) {
            event.preventDefault();
            var self = this;
            new Model('scm.repository.branch').call(method, [this.id], {'context': {'in_new_thread': true}}).then(function (result) {
                if (!result || typeof(result) === "boolean") {
                    self.trigger_up('kanban_reload');
                } else {
                    self.do_action(result);
                }
         });
        },
        branch_test: function (event) {
            this.call_branch_method(event, 'create_build');
        },
        branch_force_test: function (event) {
            this.call_branch_method(event, 'force_create_build');
        },
        branch_download_docker_image: function (event) {
            this.call_branch_method(event, 'download_docker_image');
        },
        branch_subcribe: function (event) {
            this.call_branch_method(event, 'message_subscribe_users');
        },
        branch_unsubcribe: function (event) {
            this.call_branch_method(event, 'message_unsubscribe_users');
        },
    });

    KanbanRecord.include({
        kanban_coverage_level: function(percent) {
            return parseInt(percent / 25);
        },
    });

});
