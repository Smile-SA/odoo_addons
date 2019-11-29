odoo.define('smile_todo_list.FavoriteMenu', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.BasicModel');
    var data_manager = require('web.data_manager');
    var FavoriteMenu = require('web.FavoriteMenu');
    var pyeval = require('web.py_utils');
    var session = require('web.session');
    var rpc = require('web.rpc');
    var _t = core._t;

    FavoriteMenu.include({
        start: function () {
            var res = this._super();
            var $shared_filter = this.$inputs.eq(1),
                $default_filter = this.$inputs.eq(2),
                $todo_filter = this.$inputs.eq(3),
                $todo_category = this.$el.find('#todo_category');

            rpc.query({
                  model: 'ir.filters.category',
                  method: 'search_read',
                  args: [[], ['id','name']],

                 }).then(function (categories) {
                    _.each(categories, function(category) {
                    $todo_category.append($('<option>', {value: category.id, text: category.name}));
                    });
                 });

            $todo_category.hide();
            $shared_filter.click(function () {
                $default_filter.prop('checked', false);
                $todo_filter.prop('checked', false);
                $todo_category.hide();
            });
            $default_filter.click(function () {
                $shared_filter.prop('checked', false);
                $todo_filter.prop('checked', false);
                $todo_category.hide();
            });
            $todo_filter.click(function () {
                $default_filter.prop('checked', false);
                $shared_filter.prop('checked', false);
                if ($todo_filter.is(':checked')) {
                    $todo_category.show();
                } else {
                    $todo_category.hide();
                }
            });
            return res;
        },
        save_todo: function() {
            var self = this,
                filter_name = this.$inputs[0].value,
                default_filter = this.$inputs[1].checked,
                shared_filter = this.$inputs[2].checked,
                todo_filter = this.$inputs[3].checked,
                todo_category = this.$el.find('select#todo_category').val();
            if (!filter_name.length){
                this.do_warn(_t("Error"), _t("Filter name is required."));
                this.$inputs.first().focus();
                return;
            }
            if (_.chain(this.filters)
                    .pluck('name')
                    .contains(filter_name).value()) {
                this.do_warn(_t("Error"), _t("Filter with same name already exists."));
                this.$inputs.first().focus();
                return;
            }
            var search = this.searchview.build_search_data(),
                view_manager = this.findAncestor(function (a) {
                    // HORRIBLE HACK. PLEASE SAVE ME FROM MYSELF (BUT IN A PAINLESS WAY IF POSSIBLE)
                    return 'active_view' in a;
                }),
                view_context = view_manager ? view_manager.active_view.controller.get_context() : {},
                results = pyeval.eval_domains_and_contexts({
                    domains: search.domains,
                    contexts: search.contexts.concat(view_context || []),
                    group_by_seq: search.groupbys || [],
                });
            if (!_.isEmpty(results.group_by)) {
                results.context.group_by = results.group_by;
            }
            // Don't save user_context keys in the custom filter, otherwise end
            // up with e.g. wrong uid or lang stored *and used in subsequent
            // reqs*
            var ctx = results.context;
            _(_.keys(session.user_context)).each(function (key) {
                delete ctx[key];
            });
            var filter = {
                name: filter_name,
                user_id: shared_filter ? false : session.uid,
                model_id: this.target_model,
                context: results.context,
                domain: results.domain,
                is_default: default_filter,
                todo_list: todo_filter,
                category_id: todo_category,
                action_id: this.action_id,
            };
            return data_manager.create_filter(filter).done(function (id) {
                self.toggle_save_menu(false);
                self.$save_name.find('input').val('').prop('checked', false);
            });
        },
        save_favorite: function () {
            if (this.$inputs[3].checked) {
                return this.save_todo();
            } else {
                return this._super.apply(this, arguments);
            }
        },
    });

});
