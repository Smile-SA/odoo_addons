# -*- coding: utf-8 -*-

from odoo import api, fields, models


class DiscountContractForecastMethod(models.Model):
    _name = 'discount.contract.forecast_method'
    _description = 'Forecast Method'

    name = fields.Char(required=True, translate=True)
    code = fields.Char()
    formula = fields.Text(required=True)

    @api.one
    def name_get(self):
        name = self.name
        if self.code:
            name = '[%s] %s' % (self.code, name)
        return self.id, name
