# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp
from odoo.tools.safe_eval import safe_eval


class DiscountContractLine(models.Model):
    _name = 'discount.contract.line'
    _description = 'Discount Contrat - Discount by rule'
    _rec_name = 'rule_id'

    contract_id = fields.Many2one('discount.contract', 'Contract',
                                  required=True, readonly=True,
                                  ondelete='cascade')
    rule_id = fields.Many2one('discount.contract.rule', 'Rule',
                              required=True, readonly=True,
                              ondelete='cascade')
    base_value = fields.Float(digits=dp.get_precision('Discount base value'),
                              readonly=True)
    discount_amount = fields.Monetary(readonly=True)
    currency_id = fields.Many2one(related='contract_id.currency_id',
                                  readonly=True, store=True)

    @api.multi
    def _get_period_dates(self, in_previous_period=False):
        date_start = fields.Date.from_string(self.contract_id.date_start)
        date_stop = fields.Date.from_string(self.contract_id.date_stop)
        if in_previous_period:
            delta = self.contract_id._get_contract_timedelta()
            date_start -= relativedelta(**delta)
            date_stop -= relativedelta(**delta)
        return (fields.Date.to_string(date_start),
                fields.Date.to_string(date_stop))

    @api.multi
    def _get_period_filters(self, in_previous_period=False):
        date_start, date_stop = self._get_period_dates(in_previous_period)
        return [
            ('invoice_id.date_invoice', '>=', date_start),
            ('invoice_id.date_invoice', '<', date_stop)
        ]

    @api.multi
    def _get_partner_filters(self):
        self.ensure_one()
        partner_id = self.contract_id.partner_id.id
        return [
            '|',
            ('invoice_id.partner_id', '=', partner_id),
            ('invoice_id.commercial_partner_id', '=', partner_id),
        ]

    @api.multi
    def _get_invoice_lines(self, in_previous_period=False):
        self.ensure_one()
        domain = [
            ('invoice_id.discount_contract_id', '=', False),
            ('invoice_id.state', 'in', ('open', 'paid')),
            ('invoice_id.company_id', '=', self.contract_id.company_id.id),
        ]
        domain += self._get_partner_filters()
        domain += self._get_period_filters(in_previous_period)
        domain += self.rule_id.get_filters()
        return self.env['account.invoice.line'].search(domain)

    @api.multi
    def compute_base_value(self, in_previous_period=False):
        self.ensure_one()
        invoice_lines = self._get_invoice_lines(in_previous_period)
        return self.rule_id._compute_base_value(invoice_lines)

    @api.one
    def _compute_base_value(self):
        if self.rule_id.value_type == 'growth':
            previous = self.compute_base_value(in_previous_period=True)
            if previous:
                current = self.compute_base_value()
                self.base_value = (current - previous) / previous * 100.0
        else:
            self.base_value = self.compute_base_value()

    @api.one
    def _compute_discount_amount(self):
        discount_amount = self.rule_id.compute_discount_amount(
            self.base_value)
        if isinstance(discount_amount, basestring):
            self.discount_amount = safe_eval(
                discount_amount, {'rule': self.rule_id,
                                  'invoice_lines': self._get_invoice_lines()})
        else:
            self.discount_amount = discount_amount

    @api.one
    def _update_contract_line(self):
        self._compute_base_value()
        self._compute_discount_amount()
