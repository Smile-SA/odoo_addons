# (C) 2023 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.models.ir_qweb_fields import FloatConverter, MonetaryConverter


def record_to_html_float(self, record, field_name, options):
    if 'precision' not in options and 'decimal_precision' not in options and 'digits' in record._fields[field_name].get_description(self.env):
        
        _, precision = \
            record._fields[field_name].get_description(self.env)['digits'] or \
            (None, None)
        options = dict(options, precision=precision)
        #raise Exception(precision)
    return super(FloatConverter, self).record_to_html(
        record, field_name, options)

def record_to_html_monetary(self, record, field_name, options):
    options = dict(options)
        #currency should be specified by monetary field
    field = record._fields[field_name]

    if not options.get('display_currency') and field.type == 'monetary' and field.currency_field:
        options['display_currency'] = record[field.currency_field]
    if not options.get('display_currency'):
        # search on the model if they are a res.currency field to set as default
        fields = record._fields.items()
        currency_fields = [k for k, v in fields if v.type == 'many2one' and v.comodel_name == 'res.currency']
        if currency_fields:
            options['display_currency'] = record[currency_fields[0]]
    if 'precision' not in options and 'decimal_precision' not in options and 'digits' in record._fields[field_name].get_description(self.env):
        
        _, precision = \
            record._fields[field_name].get_description(self.env)['digits'] or \
            (None, None)
        options = dict(options, precision=precision)
    #raise Exception(options)
    return super(MonetaryConverter, self).record_to_html(
        record, field_name, options)

def value_to_html_monetary(self, value, options):
        display_currency = options['display_currency']

        if not isinstance(value, (int, float)):
            raise ValueError(_("The value send to monetary field is not a number."))


        # lang.format mandates a sprintf-style format. These formats are non-
        # minimal (they have a default fixed precision instead), and
        # lang.format will not set one by default. currency.round will not
        # provide one either. So we need to generate a precision value
        # (integer > 0) from the currency's rounding (a float generally < 1.0).
        fmt = "%.{0}f".format(display_currency.display_decimal_places)

        if options.get('from_currency'):
            date = options.get('date') or fields.Date.today()
            company_id = options.get('company_id')
            if company_id:
                company = self.env['res.company'].browse(company_id)
            else:
                company = self.env.company
            value = options['from_currency']._convert(value, display_currency, company, date)

        lang = self.user_lang()
        formatted_amount = lang.format(fmt, display_currency.round(value),
                                grouping=True, monetary=True).replace(r' ', u'\N{NO-BREAK SPACE}').replace(r'-', u'-\N{ZERO WIDTH NO-BREAK SPACE}')

        pre = post = u''
        if display_currency.position == 'before':
            pre = u'{symbol}\N{NO-BREAK SPACE}'.format(symbol=display_currency.symbol or '')
        else:
            post = u'\N{NO-BREAK SPACE}{symbol}'.format(symbol=display_currency.symbol or '')

        return u'{pre}<span class="oe_currency_value">{0}</span>{post}'.format(formatted_amount, pre=pre, post=post)
FloatConverter.record_to_html = record_to_html_float
MonetaryConverter.record_to_html = record_to_html_monetary
MonetaryConverter.value_to_html = value_to_html_monetary