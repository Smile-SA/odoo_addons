# -*- coding: utf-8 -*-

from odoo import api, fields, models


class DiscountContract(models.Model):
    _inherit = 'discount.contract'

    forecast_method_id = fields.Many2one('discount.contract.forecast_method',
                                         'Forecast method')
    theoretical_discount = fields.Monetary('Theoretical discount',
                                           readonly=True)

    @api.one
    def _compute_discount_amount(self):
        super(DiscountContract, self)._compute_discount_amount()
        self.theoretical_discount = sum(self.mapped(
            'contract_line_ids.theoretical_discount'))
