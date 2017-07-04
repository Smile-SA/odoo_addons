odoo.define('smile_web_gantt.GanttView', function (require) {
    "use strict";

    var core = require('web.core');
    var GanttView = core.view_registry.get('gantt');
    var _t = core._t;

    GanttView.include({
        init: function () {
            this._super.apply(this, arguments);
            if (this.fields_view.arch.attrs.default_scale) {
                this.scale = this.fields_view.arch.attrs.default_scale;
            }
        },
        _compute_consolidation: function (task) {
            if (task.is_group) {
                var children = this._get_all_children(task.id);
                var sum = function(subtotal, task_id) {
                    return subtotal + gantt.getTask(task_id).consolidation;
                };
                return _.reduce(children, sum, 0);
            } else {
                return task.consolidation;
            }
        },
        load_gantt: function () {
            this._super.apply(this, arguments);
            var self = this;
            var native_task_text = gantt.templates.task_text;
            gantt.templates.task_text = function (start, end, task) {
                if (self.type === "gantt" && self.fields_view.arch.attrs.consolidation != undefined) {
                    var label = self.fields_view.arch.attrs.string || self.fields[self.fields_view.arch.attrs.consolidation].string
                    return self._compute_consolidation(task) + "<span class=\"half_opacity\"> " + label + "</span>";
                } else {
                    return native_task_text(start, end, task);
                }
            };
        },
        scale_zoom: function (value) {
            this._super(value);
            if (this.scale == "year" && this.fields_view.arch.attrs.year_subscale == "week") {
                gantt.config.subscales = [
                    {unit:"week", step:1, date:_t("W") + "%W"}
                ];
            }
        },
    });

});
