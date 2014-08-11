# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

from openerp import api, fields, models, _
from openerp.exceptions import Warning


class ResCurrencyRateType(models.Model):
    _name = "res.currency.rate.type"
    _description = "Currency Rate Type"

    name = fields.Char(size=64, required=True, translate=True)


class ResCurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    currency_rate_type_id = fields.Many2one('res.currency.rate.type', 'Currency Rate Type',
                                            help="Allow you to define your own currency rate types, "
                                                 "like 'Average' or 'Year to Date'. Leave empty "
                                                 "if you simply want to use the normal 'spot' rate type")


class ResCurrency(models.Model):
    _inherit = "res.currency"

    def _get_current_rate(self, cr, uid, ids, raise_on_no_rate=True, context=None):
        context = context or {}
        res = {}
        date = context.get('date') or time.strftime('%Y-%m-%d')
        # Convert False values to None ...
        currency_rate_type = context.get('currency_rate_type_id') or None
        # ... and use 'is NULL' instead of '= some-id'.
        operator = '=' if currency_rate_type else 'is'
        for id in ids:
            cr.execute('SELECT rate FROM res_currency_rate '
                       'WHERE currency_id = %%s '
                       'AND name <= %%s AND currency_rate_type_id %s %%s '
                       'ORDER BY name desc LIMIT 1' % operator,
                       (id, date, currency_rate_type))
            if cr.rowcount:
                res[id] = cr.fetchone()[0]
            elif not raise_on_no_rate:
                res[id] = 0
            else:
                currency = self.browse(cr, uid, id, context=context)
                raise Warning(_("No currency rate associated for currency '%s' for the given period") % currency.name)
        return res

    def _get_conversion_rate(self, cr, uid, from_currency, to_currency, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        ctx.update({'currency_rate_type_id': ctx.get('currency_rate_type_from')})
        from_currency = self.browse(cr, uid, from_currency.id, context=ctx)
        ctx.update({'currency_rate_type_id': ctx.get('currency_rate_type_to')})
        to_currency = self.browse(cr, uid, to_currency.id, context=ctx)

        if from_currency.rate == 0 or to_currency.rate == 0:
            date = context.get('date', time.strftime('%Y-%m-%d'))
            if from_currency.rate == 0:
                currency_symbol = from_currency.symbol
            else:
                currency_symbol = to_currency.symbol
            raise Warning(_('No rate found \n for the currency: %s \n'
                            'at the date: %s') % (currency_symbol, date))
        return to_currency.rate/from_currency.rate

    def _compute(self, cr, uid, from_currency, to_currency, from_amount, round=True, context=None):
        context = context or {}
        if to_currency.id == from_currency.id and \
                context.get('currency_rate_type_from') == context.get('currency_rate_type_to'):
            rate = 1.0
        else:
            rate = self._get_conversion_rate(cr, uid, from_currency, to_currency, context=context)
        return self.round(cr, uid, to_currency, from_amount * rate) if round else from_amount * rate

    @api.v7
    def compute(self, cr, uid, from_currency_id, to_currency_id, from_amount,
                round=True, currency_rate_type_from=False, currency_rate_type_to=False,
                context=None):
        context = context or {}
        ctx = context.copy()
        ctx.update({'currency_rate_type_from': currency_rate_type_from, 'currency_rate_type_to': currency_rate_type_to})
        return super(ResCurrency, self).compute(cr, uid, from_currency_id, to_currency_id, from_amount, round, ctx)

    @api.v8
    def compute(self, from_amount, to_currency, round=True,
                currency_rate_type_from=False, currency_rate_type_to=False):
        """ Convert `from_amount` from currency `self` to `to_currency`. """
        assert self, "compute from unknown currency"
        assert to_currency, "compute to unknown currency"
        # apply conversion rate
        if self == to_currency and currency_rate_type_from == currency_rate_type_to:
            to_amount = from_amount
        else:
            to_amount = from_amount * self._get_conversion_rate(self, to_currency)
        # apply rounding
        return to_currency.round(to_amount) if round else to_amount
