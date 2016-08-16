odoo.define('web_search_timedelta', function (require) {
    'use strict';

    var core = require('web.core');
    var _lt = core._lt;
    var search_filters = require('web.search_filters');

	search_filters.ExtendedSearchProposition.include({
		init: function (parent, fields) {
        	this._super(parent, fields);
        	this.timedelta = null;
	    },
	    select_field: function(field) {
	    	this._super(field);
	        var Field = core.search_filters_registry.get_any(["integer"]);
        	this.timedelta = new Field(this, field);
        	var $timedelta_loc = this.$('.o_searchview_extended_prop_timedelta_value').empty();
	        this.timedelta.appendTo($timedelta_loc);
	    	if (this.value.timedelta_types !== undefined)
                var self = this;
	            this.$('.o_searchview_extended_prop_timedelta_type').html('');
	    		_.each(this.value.timedelta_types, function(timedelta_type) {
		            $('<option>', {value: timedelta_type.value, format: timedelta_type.format})
		                .text(String(timedelta_type.text))
		                .appendTo(self.$('.o_searchview_extended_prop_timedelta_type'));
		        });
	    },
	    changed: function() {
	        this._super();
			var $value = this.$('.o_searchview_extended_prop_op'),
        		$timedelta = this.$('.o_searchview_extended_prop_timedelta');
        	$value.show();
        	$timedelta.hide();
	    },
		operator_changed: function (e) {
	 		this._super(e);
        	var $value = this.$('.o_searchview_extended_prop_value'),
        		$timedelta = this.$('.o_searchview_extended_prop_timedelta');
	        switch ($(e.target).val()) {
	        case '>=+':
	        case '<=+':
	        	$value.hide();
	            $timedelta.show();
	            break;
	        default:
	       		$value.show();
	            $timedelta.hide();
	        }
	    },
	});

	search_filters.ExtendedSearchProposition.DateTime.include({
        init: function () {
            this._super();
            var new_operators = [
            	{value: ">=+", text: _lt("within the last")},
            	{value: "<=+", text: _lt("more than ... ago")},
            ];
            if (_(this.operators).pluck('value').indexOf(new_operators[0].value) === -1) {
	            this.operators = this.operators.concat(new_operators);
            }
        },
        timedelta_types: [
            {value: "Y", text: _lt("years")},
            {value: "m", text: _lt("months")},
            {value: "W", text: _lt("weeks")},
            {value: "d", text: _lt("days")},
            {value: "H", text: _lt("hours")},
            {value: "M", text: _lt("minutes")},
        ],
		get_domain: function(field, operator) {
			switch (operator.value) {
				case '>=+':
				case '<=+':
					var $prop = this.$el.parent().parent() 
					var timedelta_value = $prop.find('.o_searchview_extended_prop_timedelta_value input').val();
					var timedelta_type = $prop.find('.o_searchview_extended_prop_timedelta_type').val();
					return [[field.name, operator.value.replace('+', ''), timedelta_value + timedelta_type]];
				default:
					return this._super(field, operator);
			}
		},
		get_label: function (field, operator) {
			switch (operator.value) {
				case '>=+':
				case '<=+':
					var $prop = this.$el.parent().parent() 
					var timedelta_value = $prop.find('.o_searchview_extended_prop_timedelta_value input').val();
					var timedelta_type = $prop.find('.o_searchview_extended_prop_timedelta_type').find(":selected").text();
					var formats_by_operator = {
						'>=+': _lt("within the last %(timedelta_value)s %(timedelta_type)s"),
						'<=+': _lt("more than %(timedelta_value)s %(timedelta_type)s ago"),
					};
					return _.str.sprintf('%(field)s ' + formats_by_operator[operator.value],
										 {field: field.string, timedelta_value: timedelta_value, timedelta_type: timedelta_type});
				default: 
					return this._super(field, operator);
			}
		},
	});

	search_filters.ExtendedSearchProposition.Date.include({
        timedelta_types: [
            {value: "Y", text: _lt("years")},
            {value: "m", text: _lt("months")},
            {value: "W", text: _lt("weeks")},
            {value: "d", text: _lt("days")},
        ],
	});

});
