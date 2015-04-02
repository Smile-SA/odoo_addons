openerp.smile_web_search_range = function(instance) {

	var _t =  instance.web._t,
		_lt = instance.web._lt;

	instance.web.search.ExtendedSearchProposition.include({
		init: function (parent, fields) {
        	this._super(parent, fields);
        	this.value2 = null;
	    },
	    select_field: function(field) {
        	this._super(field);
	        var Field = instance.web.search.custom_filters.get_object(field.type);
        	this.value2 = new Field(this, field);
        	var $value2_loc = this.$('.searchview_extended_prop_value2').hide().empty();
	        this.value2.appendTo($value2_loc);
	    },
	    changed: function() {
	        this._super();
        	var $value2 = this.$('.searchview_extended_prop_value2');
        	$value2.hide();
	    },
		operator_changed: function (e) {
	 		this._super(e);
        	var $value2 = this.$('.searchview_extended_prop_value2');
	        switch ($(e.target).val()) {
	        case '><':
	            $value2.show();
	            break;
	        default:
	            $value2.hide();
	        }
	    },
	    get_proposition: function() {
	    	proposition = this._super();
	    	if (proposition === null) {
	    		return null;
	    	}
	    	var field = this.attrs.selected;
	        var op_select = this.$('.searchview_extended_prop_op')[0];
	        var operator = op_select.options[op_select.selectedIndex];
	        if (operator.value == '><') {
	        	var value1 = this.value.get_domain(field, operator)[2];
		        var value2 = this.value2.get_domain(field, operator)[2];
		        var operators = [
		        	{value: ">=", text: _lt("greater or equal than")},
		        	{value: "<=", text: _lt("less or equal than")},
		        ];
		        if (value1 && value2) {
			        proposition['label'] += _.str.sprintf(' and "%(value)s"', {value: value2});
			        proposition['value'][2] = [value1, value2];
			    } else {
			    	var value = value1 || value2;
			    	var new_operator = (value2) ? operators[1] : operators[0];
			    	var arguments = {field: field.string, operator: new_operator.text, value: value};
			        proposition['label'] = _.str.sprintf('%(field)s %(operator)s "%(value)s"', arguments);
			    	proposition['value'] = [field.name, new_operator.value, value];
			    }
			}
	        return proposition;
	    }
	});

	instance.web.search.ExtendedSearchProposition.DateTime.include({
        init: function () {
            this._super();
            var new_operator = {value: "><", text: _lt("between")};
            if (_(this.operators).pluck('value').indexOf(new_operator.value) === -1) {
	            this.operators.push(new_operator);
            }
        },
	});

	instance.web.search.ExtendedSearchProposition.Float.include({
        init: function () {
            this._super();
            var new_operator = {value: "><", text: _lt("between")};
            if (_(this.operators).pluck('value').indexOf(new_operator.value) === -1) {
	            this.operators.push(new_operator);
            }
        },
	});

	instance.web.search.ExtendedSearchProposition.Integer.include({
        init: function () {
            this._super();
            var new_operator = {value: "><", text: _lt("between")};
            if (_(this.operators).pluck('value').indexOf(new_operator.value) === -1) {
	            this.operators.push(new_operator);
            }
        },
	});

};
