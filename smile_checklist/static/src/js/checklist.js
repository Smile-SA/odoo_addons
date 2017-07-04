odoo.define('checklist.checklist_instance', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var QWeb = core.qweb;
    var Widget = require('web.Widget');

    var checklistInstanceView = Widget.extend({
        template: 'Checklist',
        init: function(parent, context) {
            this._super(parent, context);
            this.res_model = context.context.res_model;
            this.res_id = context.context.res_id;
        },
        start: function () {
            var self = this;
            new Model('checklist.task.instance')
                .query(['name', 'progress_rate', 'mandatory', 'fields_to_fill', 'fields_filled'])
                .filter([['model', '=', self.res_model], ['res_id', '=', self.res_id]])
                .all()
                .then(function (tasks) {
                    _(tasks).each(function (task) {
                        self.$el.append(QWeb.render('ChecklistTask', {task: task}));
                    });
                });
        },
    });

    core.action_registry.add('checklist_instance_view', checklistInstanceView);
    return {
        checklistInstanceView: checklistInstanceView,
    }

});
