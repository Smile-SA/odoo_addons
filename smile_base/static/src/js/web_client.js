openerp.smile_base = function(instance) {

	// Copyright initOS GmbH & Co. KG - module web_list_html_widget
    instance.web.list.columns.map['field.html'] = 'instance.web.list.Html';
    instance.web.list.Html = instance.web.list.Column.extend({
        _format: function (row_data, options) {
            return instance.web.format_value(
                row_data[this.id].value, this, options.value_if_empty);
        }
    });

	// Copyright Therp BV - Module disable_openerp_online
    instance.web.WebClient.include({
        show_annoucement_bar: function() {
        	return;
        }
    });

	// Color navbar
	instance.web.WebClient.include({
        set_title: function() {
            this._super();
            var config_parameter = new instance.web.Model('ir.config_parameter');
            config_parameter.call('get_param', ['server.environment', 'prod']).then(function(server_env) {
                if (server_env != 'prod') {
			        $(".navbar-inverse").css({'background-color': '#DA0303', 'border-color': '#DA0303'});
			        $(".navbar-inverse .navbar-nav > li > a").css({'color': '#edd', 'background-color': '#DA0303'});
			        $(".navbar-inverse .navbar-nav > .active > a").css({'color': '#fff', 'background-color': '#CF0202'});
				}
		    });
		
        }
    });

	// Max upload size: default 25Mo
	instance.web.form.FieldBinary.include({
        init: function(field_manager, node) {
        	var self = this;
            this._super(field_manager, node);
            var config_parameter = new instance.web.Model('ir.config_parameter');
            config_parameter.call('get_param', ['max_upload_size', 25]).then(function(max_upload_size) {
            	self.max_upload_size = max_upload_size * 1024 * 1024;
            });
        }
    });

};
