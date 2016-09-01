odoo.define('web_search_range', function (require) {
    'use strict';

    var core = require('web.core');
    var _t = core._t;
    var _lt = core._lt;
    var search_filters = require('web.search_filters');

	search_filters.ExtendedSearchProposition.include({
		init: function (parent, fields) {
        	this._super(parent, fields);
        	this.value2 = null;
	    },
	    select_field: function(field) {
        	this._super(field);
	        var Field = core.search_filters_registry.get_any([field.type, "char"]);
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
	    get_filter: function() {
	    	var condition = this._super();
	    	if (condition === null) {
	    		return null;
	    	}
	    	var field = this.attrs.selected,
	            op_select = this.$('.searchview_extended_prop_op')[0],
	            operator = op_select.options[op_select.selectedIndex];
	        if (operator.value == '><') {
	        	var value1 = this.value.get_domain(field, operator)[2],
		            value2 = this.value2.get_domain(field, operator)[2],
		            operators = [
                        {value: ">=", text: _lt("greater or equal than")},
                        {value: "<=", text: _lt("less or equal than")},
                    ];
		        if (value1 && value2) {
					var formated_value2 = openerp.web.format_value(value2, {type: field.type});;
			        condition['attrs']['string'] += _.str.sprintf(_t(' and "%(value)s"'), {value: formated_value2});
                    var first_condition = condition['attrs']['domain'][0].slice();
                    var second_condition = condition['attrs']['domain'][0].slice();
                    first_condition[1] = ">=";
                    second_condition[1] = "<=";
                    second_condition[2] = value2;
			        condition['attrs']['domain'] = ['&', first_condition, second_condition];
			    } else {
			    	var value = value1 || value2,
			    	    new_operator = (value2) ? operators[1] : operators[0],
			    	    args = {field: field.string, operator: new_operator.text, value: value};
			        condition['attrs']['string'] = _.str.sprintf('%(field)s %(operator)s "%(value)s"', args);
			    	condition['attrs']['domain'][0] = [field.name, new_operator.value, value];
			    }
			}
	        return condition;
	    }
	});

    search_filters.ExtendedSearchProposition.DateTime.include({
        init: function () {
            this._super();
            var new_operator = {value: "><", text: _lt("between")};
            if (_(this.operators).pluck('value').indexOf(new_operator.value) === -1) {
	            this.operators.push(new_operator);
            }
        },
	});

	search_filters.ExtendedSearchProposition.Float.include({
        init: function () {
            this._super();
            var new_operator = {value: "><", text: _lt("between")};
            if (_(this.operators).pluck('value').indexOf(new_operator.value) === -1) {
	            this.operators.push(new_operator);
            }
        },
	});

	search_filters.ExtendedSearchProposition.Integer.include({
        init: function () {
            this._super();
            var new_operator = {value: "><", text: _lt("between")};
            if (_(this.operators).pluck('value').indexOf(new_operator.value) === -1) {
	            this.operators.push(new_operator);
            }
        },
	});

});
