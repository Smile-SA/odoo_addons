# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.float_utils import float_round


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    industry_id = fields.Many2one(
        'res.partner.industry', 'Industry',
        required=True, ondelete='restrict')
    deduction_rate = fields.Float(
        digits=(13, 12), compute='_compute_price', store=True)
    price_tax_d = fields.Monetary(
        'Deductible tax', compute='_compute_price', store=True)
    price_total_nd = fields.Monetary(
        'Non deductible amount', compute='_compute_price', store=True,
        help="Total amount without deductible taxes")

    @api.one
    @api.depends('industry_id', 'product_id', 'invoice_id.date_invoice')
    def _compute_price(self):
        super(AccountInvoiceLine, self)._compute_price()
        self.deduction_rate = self.env['account.tax.rate']. \
            _compute_deduction_rate(
                self.industry_id, self.product_id.product_tmpl_id,
                self.invoice_id.date_invoice)
        price_tax = self.price_total - self.price_subtotal
        currency = self.currency_id or self.company_id.currency_id
        self.price_tax_d = float_round(price_tax * self.deduction_rate,
                                       currency.decimal_places)
        self.price_total_nd = self.price_total - self.price_tax_d
