openerp.smile_todo_list = function(instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.web.search.SaveFilter.include({
        start: function() {
            var self = this;
            this.model = new instance.web.Model('ir.filters');
            this.$el.on('submit', 'form', this.proxy('save_current'));
            this.$el.on('click', 'input[type=checkbox]', function() {
                $(this).siblings('input[type=checkbox]').prop('checked', false);
                if (self.$('#oe_searchview_todo').prop('checked')) {
                    self.$('#oe_searchview_categories').show();
                } else {
                    self.$('#oe_searchview_categories').hide();
                }
            });
            this.$el.on('click', 'h4', function() {
                self.$el.toggleClass('oe_opened');
            });
            // Add todo checkbox and list of available todo categories
            this.$el.find('p').last().append(
                "<input id=\"oe_searchview_todo\" type=\"checkbox\" />" +
                "<label for=\"oe_searchview_todo\">Todo list</label>"
            );
            var category_list = "<select id=\"oe_searchview_categories\" style=\"margin-left: 10px\">";
            new instance.web.Model('ir.filters.category').query(['id', 'name']).all().then(function(categories) {
                _.each(categories, function(category) {
                    category_list += "<option value=\"" + category.id + "\">" + category.name + "</option>";
                });
                category_list += "</select>";
                self.$el.find('p').last().append(category_list);
                self.$('#oe_searchview_categories').hide();
            });
        },
        save_current: function() {
            var self = this;
            var $name = this.$('input:first');
            var private_filter = !this.$('#oe_searchview_custom_public').prop('checked');
            var set_as_default = this.$('#oe_searchview_custom_default').prop('checked');
            var set_as_todo = this.$('#oe_searchview_todo').prop('checked');

            if (_.isEmpty($name.val())) {
                this.do_warn(_t("Error"), _t("Filter name is required."));
                return false;
            }

            var category_id = false;
            if (set_as_todo) {
                category_id = this.$('#oe_searchview_categories').val();
            }

            var search = this.view.build_search_data();
            instance.web.pyeval.eval_domains_and_contexts({
                domains: search.domains,
                contexts: search.contexts,
                group_by_seq: search.groupbys || []
            }).done(
                function(results) {
                    if (!_.isEmpty(results.group_by)) {
                        results.context.group_by = results.group_by;
                    }
                    // Don't save user_context keys in the custom filter,
                    // otherwise end up with e.g. wrong uid or lang stored *and used in subsequent reqs*
                    var ctx = results.context;
                    _(_.keys(instance.session.user_context)).each(
                        function(key) {
                            delete ctx[key];
                        });
                    debugger;
                    var filter = {
                        name: $name.val(),
                        user_id: (private_filter) ? instance.session.uid : false,
                        model_id: self.view.model,
                        context: results.context,
                        domain: results.domain,
                        is_default: set_as_default,
                        todo_list: set_as_todo,
                        category_id: category_id,
                        action_id: self.custom_filters.get_action_id()
                    };
                    // FIXME: current context?
                    return self.model.call('create_or_replace', [filter]).done(
                        function(id) {
                            filter.id = id;
                            if (self.custom_filters) {
                                self.custom_filters.append_filter(filter);
                            }
                            self.$el.removeClass('oe_opened').find('form')[0].reset();
                        }
                    );
                });
            return false;
        },
    });
};
