openerp.web_colored = function (instance) {

  instance.web.form.FieldColored = instance.web.form.FieldFloat.extend({

    set_value: function(value_) {
        this._super.apply(this, [value_]);
        this.change_color(value_);
    },
    render_value: function() {
        this._super();
        value_ = this.get('value');
        this.change_color(value_);
    },
    change_color: function(value_) {
      var colored = JSON.parse(this.node.attrs.modifiers || '{}').colored || "{}";
      if (value_) {
          for (var color in colored)
          {
          	var expr = colored[color];
          	expr_bool = eval(value_ + expr);
          	if (expr_bool == true) {
          		this.$el.find('span').attr('style', "color:"+color)
          		return;
          	}
          }
        }
        this.$el.find('span').removeAttr('style');
    },

  });

  instance.web.form.widgets.add('colored', 'instance.web.form.FieldColored');

  //########################################################

  instance.web.list.ColoredColumn = instance.web.list.Column.extend({
    init: function (id, tag, attrs) {
        _.extend(attrs, {
            id: id,
            tag: tag
        });

        this.modifiers = attrs.modifiers ? JSON.parse(attrs.modifiers) : {};
        delete attrs.modifiers;
        _.extend(this, attrs);

        if (this.modifiers['tree_invisible']) {
            this.invisible = '1';
        } else { delete this.invisible; }

        if (this.modifiers['colored']) {
            this.colored = this.modifiers['colored'];
        } else { this.colored = {}; }
    },

    _format: function (row_data, options) {
        if (row_data[this.id].value) {
          for (var color in this.colored)
          {
          	var expr = this.colored[color];
          	expr_bool = eval(row_data[this.id].value + expr);
          	if (expr_bool == true) {
          		return _.str.sprintf('<span style="color:%s">%s</span>', color, row_data[this.id].value);
          	}
          }
        }
        return _.escape(instance.web.format_value(
            row_data[this.id].value, this, options.value_if_empty));
    },
  });

  instance.web.list.columns.add('field.colored', 'instance.web.list.ColoredColumn');

};
