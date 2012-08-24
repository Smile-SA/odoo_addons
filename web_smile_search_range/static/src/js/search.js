openerp.web_smile_search_range = function(openerp) {
var QWeb = openerp.web.qweb,
      _t =  openerp.web._t,
     _lt = openerp.web._lt;

// XXX Too much code duplication in here IMHO. Should be cleaned as soon as we get better in JS ! ;)

openerp.web.search.FloatField = openerp.web.search.FloatField.extend({
    start: function () {
        this._super();
        this.input2_id = this.element_id + "_2";
        this.input2_name = this.attrs.name + "_2";
        this.input2_value = this.defaults[this.input2_name] || false;
        this.$element.after(' - <input type="text" id="' + this.input2_id + '"/>');
        this.$element.parent().find('#' + this.input2_id).attr({
            size: '15',
            name: this.input2_name,
            value: this.input2_value || '',
        });
    },
    get_value2: function () {
        var input2_el = this.$element.parent().find('#' + this.input2_id);
        if (!input2_el.val()) {
            return null;
        }
        var val = this.parse(input2_el.val()),
          check = Number(input2_el.val());
        if (isNaN(val) || val !== check) {
            input2_el.addClass('error');
            throw new openerp.web.search.Invalid(
                this.attrs.name, input2_el.val(), this.error_message);
        }
        input2_el.removeClass('error');
        return val;
    },
    get_domain: function () {
        var val = this.get_value();
        var val2 = this.get_value2();
        if ((val === null || val === '') && (val2 === null || val2 === '')) {
            return;
        }
        return this.make_domain(this.attrs.name, val, val2);
    },
    make_domain: function (name, value1, value2) {
        if (value1 != null && value1 != '' && value2 != null && value2 != '') {
            return ['&', [name, '>=', value1],
                         [name, '<=', value2]];
        } else if (value1 != null && value1 != '') {
            return [[name, '>=', value1]];
        } else {
            return [[name, '<=', value2]];
        }
    },
});

openerp.web.search.DateField = openerp.web.search.DateField.extend({
    start: function () {
        this._super();
        this.$element.append(' - ');
        this.datewidget2 = new openerp.web.DateWidget(this);
        this.datewidget2.appendTo(this.$element);
        this.datewidget2.$element.find("input")
            .attr("size", 15)
            .removeAttr('style');
        this.datewidget2.set_value(this.defaults[this.attrs.name] || false);
    },
    get_value2: function () {
        return this.datewidget2.get_value() || null;
    },
    clear: function () {
        this._super();
        this.datewidget2.set_value(false);
    },
    get_domain: function () {
        var val = this.get_value();
        var val2 = this.get_value2();
        if ((val === null || val === '') && (val2 === null || val2 === '')) {
            return;
        }
        return this.make_domain(this.attrs.name, val, val2);
    },
    make_domain: function (name, value1, value2) {
        if (value1 != null && value1 != '' && value2 != null && value2 != '') {
            return ['&', [name, '>=', value1],
                         [name, '<=', value2]];
        } else if (value1 != null && value1 != '') {
            return [[name, '>=', value1]];
        } else {
            return [[name, '<=', value2]];
        }
    },
});

openerp.web.search.DateTimeField = openerp.web.search.DateField.extend({
    // Instead of the date widget, let search datetime fields use the datetime wiget (which was the default for OpenERP 6.0 and early)
    start: function () {
        this._super();
        // Remove all default date widget
        this.$element.find(".oe_datepicker_root").remove();
        // Build range's start datetime widget
        this.datewidget = new openerp.web.DateTimeWidget(this);
        this.datewidget.prependTo(this.$element);
        this.datewidget.$element.find("input")
            .attr("size", 15)
            .attr("autofocus", this.attrs.default_focus === '1' ? 'autofocus' : null)
            .removeAttr('style');
        this.datewidget.set_value(this.defaults[this.attrs.name] || false);
        // Build range's end datetime widget
        this.datewidget2 = new openerp.web.DateTimeWidget(this);
        this.datewidget2.appendTo(this.$element);
        this.datewidget2.$element.find("input")
            .attr("size", 15)
            .removeAttr('style');
        this.datewidget2.set_value(this.defaults[this.attrs.name] || false);
    },
});

};