openerp.web_smile_colored = function (instance) {
	//TODO: use instance.web.form.compute_domain !!

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
      var modifiers = JSON.parse(this.node.attrs.modifiers || '{}');
      if (value_) {
        for (var modifier in modifiers) {
          //Check if modifier ends with _colored
          if (modifier.slice(-8) == '_colored') {
          	// Get the color prefix as 'blue' in 'blue_colored'
            var color = modifier.slice(0, -8);
	        var expr = modifiers[modifier];
	        
	        if (this.view.compute_domain(expr)) {
	      	  this.$el.find('span').attr('style', "color:"+color)
              return;
	      	}
	      }
        }
	  }
      this.$el.find('span').removeAttr('style');
    },

  });

  instance.web.form.widgets.add('colored', 'instance.web.form.FieldColored');

  //########################################################

  instance.web.list.ColoredColumn = instance.web.list.Column.extend({
    _format: function (row_data, options) {

        for (var modifier in this.modifiers) {
          //Check if modifier ends with _colored
          if (modifier.slice(-8) == '_colored') {
            // Get the color prefix as 'blue' in 'blue_colored'
            var color = modifier.slice(0, -8);
	        var expr = this.modifiers[modifier];
           if (instance.web.form.compute_domain(expr, row_data)) {
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
