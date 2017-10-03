# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp
from odoo.tools.safe_eval import safe_eval


class DiscountContractLine(models.Model):
    _inherit = 'discount.contract.line'

    theoretical_base = fields.Float(readonly=True, digits=dp.get_precision(
                                    'Discount base value'))
    theoretical_discount = fields.Monetary(readonly=True)

    @api.multi
    def _get_eval_context(self):
        return {
            'self': self,
            'fields': fields,
            'relativedelta': relativedelta,
        }

    @api.one
    def _compute_theoretical_base(self):
        formula = self.contract_id.forecast_method_id.formula
        if formula:
            eval_context = self._get_eval_context()
            self.theoretical_base = safe_eval(formula, eval_context)
        else:
            self.theoretical_base = 0.0

    @api.one
    def _compute_theoretical_discount(self):
        self.theoretical_discount = self.rule_id.compute_discount_amount(
            self.theoretical_base)

    @api.one
    def _update_contract_line(self):
        super(DiscountContractLine, self)._update_contract_line()
        self._compute_theoretical_base()
        self._compute_theoretical_discount()

    @api.multi
    def _get_period_dates(self, in_previous_period=False):
        date_start, date_stop = super(DiscountContractLine,
                                      self)._get_period_dates(
                                          in_previous_period)
        if self._context.get('force_date_start'):
            date_start = self._context['force_date_start']
        if self._context.get('force_date_stop'):
            date_stop = self._context['force_date_stop']
        return date_start, date_stop
