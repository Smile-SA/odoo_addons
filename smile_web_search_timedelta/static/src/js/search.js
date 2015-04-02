openerp.smile_web_search_timedelta = function(instance) {

	var _t =  instance.web._t,
		_lt = instance.web._lt;

	instance.web.search.ExtendedSearchProposition.include({
		init: function (parent, fields) {
        	this._super(parent, fields);
        	this.timedelta = null;
	    },
	    select_field: function(field) {
	    	this._super(field);
	        var Field = instance.web.search.custom_filters.get_object('integer');
        	this.timedelta = new Field(this, field);
        	var $timedelta_loc = this.$('.searchview_extended_prop_timedelta_value').empty();
	        this.timedelta.appendTo($timedelta_loc);
	    	if (this.value.timedelta_types !== undefined)
	            this.$('.searchview_extended_prop_timedelta_type').html('');
	    		_.each(this.value.timedelta_types, function(timedelta_type) {
		            $('<option>', {value: timedelta_type.value, format: timedelta_type.format})
		                .text(String(timedelta_type.text))
		                .appendTo(this.$('.searchview_extended_prop_timedelta_type'));
		        });
	    },
	    changed: function() {
	        this._super();
			var $value = this.$('.searchview_extended_prop_value'),
        		$timedelta = this.$('.searchview_extended_prop_timedelta');
        	$value.show();
        	$timedelta.hide();
	    },
		operator_changed: function (e) {
	 		this._super(e);
        	var $value = this.$('.searchview_extended_prop_value'),
        		$timedelta = this.$('.searchview_extended_prop_timedelta');
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
	    get_proposition: function() {
	    	proposition = this._super();
	    	if (proposition === null) {
	    		return null;
	    	}
	    	var field = this.attrs.selected;
	        var op_select = this.$('.searchview_extended_prop_op')[0];
	        var operator = op_select.options[op_select.selectedIndex];
	        if (['>=+', '<=+'].indexOf(operator.value) !== -1) {
	        	var timedelta_value = this.timedelta.$el.val();
		        var ttype_select = this.$('.searchview_extended_prop_timedelta_type')[0];
		        var timedelta_type = ttype_select.options[ttype_select.selectedIndex];
	        	var timedelta_label = timedelta_value + ' ' + (timedelta_type.label || timedelta_type.text);
	        	timedelta_value += timedelta_type.value;
	        	var formats_by_operator = {
	        		'>=+': _lt("within the last %(timedelta)s"),
	        		'<=+': _lt("more than %(timedelta)s ago"),
	        	};
		        proposition['label'] = _.str.sprintf('%(field)s ' + formats_by_operator[operator.value],
		        									 {field: field.string, timedelta: timedelta_label});
		    	proposition['value'] = [field.name, operator.value.replace('+', ''), timedelta_value];
		    }
	        return proposition;
	    }
	});

	instance.web.search.ExtendedSearchProposition.DateTime.include({
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
	});

	instance.web.search.ExtendedSearchProposition.Date.include({
        timedelta_types: [
            {value: "Y", text: _lt("years")},
            {value: "m", text: _lt("months")},
            {value: "W", text: _lt("weeks")},
            {value: "d", text: _lt("days")},
        ],
	});

};
