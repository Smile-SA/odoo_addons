# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class MonetaryConverter(models.AbstractModel):
    _inherit = 'ir.qweb.field.monetary'

    @api.model
    def value_to_html(self, value, options):
        """ Use the new field display_decimal_places instead of
        native field decimal_places to compute fmt
        """
        display_currency = options['display_currency']

        # lang.format mandates a sprintf-style format. These formats are non-
        # minimal (they have a default fixed precision instead), and
        # lang.format will not set one by default. currency.round will not
        # provide one either. So we need to generate a precision value
        # (integer > 0) from the currency's rounding (a float generally < 1.0).
        fmt = "%.{0}f".format(display_currency.display_decimal_places)

        if options.get('from_currency'):
            value = options['from_currency'].compute(value, display_currency)

        lang = self.user_lang()
        formatted_amount = lang.format(
            fmt, display_currency.round(value),
            grouping=True, monetary=True
        ).replace(r' ', u'\N{NO-BREAK SPACE}').replace(
            r'-', u'-\N{ZERO WIDTH NO-BREAK SPACE}')

        pre = post = u''
        if display_currency.position == 'before':
            pre = u'{symbol}\N{NO-BREAK SPACE}'.format(
                symbol=display_currency.symbol or '')
        else:
            post = u'\N{NO-BREAK SPACE}{symbol}'.format(
                symbol=display_currency.symbol or '')

        return u'{pre}<span class="oe_currency_value">{0}</span>{post}'.format(
            formatted_amount, pre=pre, post=post)
