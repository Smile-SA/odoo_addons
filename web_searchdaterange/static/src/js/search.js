openerp.web_searchdaterange = function(openerp) {
var QWeb = openerp.web.qweb,
      _t =  openerp.web._t,
     _lt = openerp.web._lt;

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
        this.datewidget.set_value(false);
        this.datewidget2.set_value(false);
    },
    get_domain: function () {
        var val = this.get_value();
        var val2 = this.get_value2();
        if ((val === null || val === '') && (val2 === null || val2 === '')) {
            return;
        }
        var domain = this.attrs['filter_domain'];
        return this.make_domain2(this.attrs.name, val, val2);
        return _.extend({}, domain, {own_values: {self: val}});
    },
    make_domain2: function (name, value1, value2) {
        if (value1 != null && value1 != '' && value2 != null && value2 != '') {
            return ['&', [name, '>=', value1],
                         [name, '<=', value2]];
        } else if (value1 != null && value1 != '') {
            return [[name, '>=', value1]];
        } else {
            return [[name, '<=', value2]];
        }
    }
});

openerp.web.search.DateTimeField = openerp.web.search.DateField.extend({
    make_domain2: function (name, value1, value2) {
        if (value1 != null && value1 != '') {
            value1 = value1 + ' 00:00:00';
        }
        if (value2 != null && value2 != '') {
            value2 = value2 + ' 23:59:59';
        }
        return this._super(name, value1, value2);
    }
});

};
