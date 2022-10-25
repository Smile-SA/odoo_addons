odoo.define('checklist.checklist_instance', function (require) {
    "use strict";
    var core = require('web.core');
    var QWeb = core.qweb;
    var rpc = require('web.rpc');
    var AbstractAction = require('web.AbstractAction');

    var checklistInstanceView = AbstractAction.extend({
        contentTemplate: 'Checklist',
        init: function (parent, context) {
            this._super.apply(this, arguments);
            this.res_model = context.context.res_model;
            this.res_id = context.context.res_id;
        },
        start: function () {
            var self = this;
            rpc.query({
                model: 'checklist.task.instance',
                method: 'search_read',
                domain: [
                    ['task_id.checklist_id.model_id.model', '=', self.res_model],
                    ['res_id', '=', self.res_id],
                ],
                fields: ['name', 'complete', 'mandatory'],
            }).then(function (tasks) {
                _(tasks).each(function (task) {
                    self.$el.append(QWeb.render('ChecklistTask', {task: task}));
                });
            });
        },
    });
    core.action_registry.add('checklist_instance_view', checklistInstanceView);
    return {
        checklistInstanceView: checklistInstanceView,
    };
});
