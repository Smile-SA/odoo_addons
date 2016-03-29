odoo.define('draggable_kanban_record', function (require) {
    'use strict';

    var KanbanView = require('web_kanban.KanbanView');
    var KanbanColumn = require('web_kanban.Column');

    KanbanView.include({
        get_column_options: function () {
            var result = this._super();
            result['records_draggable'] = this.is_action_enabled('record_drag');
            result['draggable'] = this.is_action_enabled('group_drag');
            return result;
        },
        render_grouped: function (fragment) {
            this._super(fragment);
            var column_options = this.get_column_options();
            if (!column_options['draggable']) {
                this.$el.sortable("destroy");
            }
        },
    });

    KanbanColumn.include({
        init: function(parent, group_data, options, record_options) {
            this._super(parent, group_data, options, record_options);
            this.records_draggable = options.records_draggable;
        },
        start: function() {
            this._super();
            if (!this.records_draggable) {
                this.$el.sortable("destroy");
            }
        },
    });

});
