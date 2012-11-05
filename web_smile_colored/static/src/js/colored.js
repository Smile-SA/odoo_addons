openerp.web_smile_colored = function (openerp) {

  openerp.web.form.FieldColored = openerp.web.form.FieldFloat.extend({

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
      var input = this.$element.find('input');
      if (value_) {
          for (var color in colored)
          {
          	var expr = colored[color];
          	expr_bool = eval(value_ + expr);
          	if (expr_bool == true) {
          		input.attr('style', "color:"+color+"; width: 100%");
          		return;
          	}
          }
        }
      if (input.style) {
      	input.style.color = '';
      }
    },

  });

  openerp.web.form.widgets.add('colored', 'openerp.web.form.FieldColored');
  
  //########################################################
  
  openerp.web.page.FieldColoredReadonly = openerp.web.page.FieldFloatReadonly.extend({
    

    set_value: function(value) {
      var colored = JSON.parse(this.node.attrs.modifiers || '{}').colored || "{}";
      var div = this.$element.find('div');
      if (value) {
          for (var color in colored)
          {
          	var expr = colored[color];
          	expr_bool = eval(value + expr);
          	if (expr_bool == true) {
          		if (!div.style) {
          			div.attr('style', 'color:' + color + "; width: 100%");
          		}
          		else {
          			div.style.color=color;
          		}
          		return this._super(value, this, '');
          	}
          }
        }
        if (div.style) {
        	div.style.color='';
        }
        return this._super(value, this, '');
    },
    });
    
  openerp.web.page.readonly.add('colored', 'openerp.web.page.FieldColoredReadonly');

  //########################################################
  var old_format_cell = openerp.web.format_cell;
  
  openerp.web.format_cell = function (row_data, column, options) {
  	options = options || {};
    var attrs = {};
    if (options.process_modifiers !== false) {
        attrs = column.modifiers_for(row_data);
    }
    if (attrs.invisible) { return ''; }

    if ((column.tag === 'button') || (!row_data[column.id])) {
    	return old_format_cell(row_data, column, options);
    }
    
    if (column.widget == 'colored') {
    	var colored = JSON.parse(column.modifiers || '{}').colored;
   	    if (row_data[column.id].value && colored) {
            for (var color in colored)
            {
          	    var expr = colored[color];
          	    expr_bool = eval(row_data[column.id].value + expr);
          	    if (expr_bool == true) {
          		    return _.str.sprintf('<span style="color:%s">%s</span>', color, row_data[column.id].value);
          	    }
            }
        }
    }
    return old_format_cell(row_data, column, options);
  };


};
