odoo.define('web_auto_refresh', function (require) {
	"use strict";
    var WebClient = require('web.WebClient');
//    var bus = require('bus.bus')
require('bus.BusService');

    WebClient.include({
        init: function(parent, client_options){
            this._super(parent, client_options);
            this.known_bus_channels = [];
            this.known_bus_events = [];
        },
        show_application: function() {
            this._super();
            this.start_polling();
        },
        on_logout: function() {
            var self = this;
            this.call('bus_service', 'offNotification', this, this.bus_notification);
            _(this.known_bus_channels).each(function (channel) {
                this.call('bus_service', 'deleteChannel', channel);
            });
            _(this.known_bus_events).each(function(e) {
                self.bus_off(e[0], e[1]);
            });
            this._super();
        },
        start_polling: function() {
            this.declare_bus_channel();
            this.call('bus_service', 'onNotification', this, this.bus_notification);
            this.call('bus_service', 'startPolling');
        },
        bus_notification: function(notification) {
            if (typeof(notification[0]) != 'undefined') {
                var channel = notification[0][0];
                if (this.known_bus_channels.indexOf(channel) != -1) {
                    var message = notification[0][1];
                    this.call('bus_service', 'trigger', channel, message);
                }
            }
        },
        bus_on: function(eventname, eventfunction) {
            console.log(eventname, eventfunction);
            this.call('bus_service', 'on', eventname, this, eventfunction);
            this.known_bus_events.push([eventname, eventfunction]);
        },
        bus_off: function(eventname, eventfunction) {
            this.call('bus_service', 'on', eventname, this, eventfunction);
            var index = _.indexOf(this.known_bus_events, (eventname, eventfunction));
            this.known_bus_events.splice(index, 1);
        },
        declare_bus_channel: function() {
            var self = this, channel = "auto_refresh";
            this.bus_on(channel, function(message) {
                var widget = self.action_manager;
                if (widget) {
                    if (message.includes('#')) {
                        widget.do_action({
                            "type": "ir.actions.act_url",
                            "url": message,
                            "target": "self",
                        });
                    } else if (typeof(widget.controllers) != 'undefined') {
                        var controller = widget.getCurrentController();
                        var action = widget.getCurrentAction();
                        if (action.auto_search && controller.widget.modelName == message && controller.widget.mode != "edit") {
                            controller.widget.reload();
                        }
                    }
                }
            });

			this.add_bus_channel(channel);
        },
        add_bus_channel: function(channel) {
            if (this.known_bus_channels.indexOf(channel) == -1) {
                this.call('bus_service', 'addChannel', channel);
                this.known_bus_channels.push(channel);
            }
        },
    })
})
