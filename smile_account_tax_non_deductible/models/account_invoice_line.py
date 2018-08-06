# -*- coding: utf-8 -*-
# (C) 2013 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.float_utils import float_round


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    industry_id = fields.Many2one(
        'res.partner.industry', 'Industry',
        required=False, ondelete='restrict')
    deduction_rate = fields.Float(
        digits=(13, 12), compute='_compute_price', store=True)
    price_tax_d = fields.Monetary(
        'Deductible tax', compute='_compute_price', store=True)
    price_total_nd = fields.Monetary(
        'Non deductible amount', compute='_compute_price', store=True,
        help="Total amount without deductible taxes")

    @api.one
    @api.depends(
        'price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
        'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id',
        'invoice_id.company_id', 'invoice_id.date_invoice', 'invoice_id.date',
        'industry_id')
    def _compute_price(self):
        super(AccountInvoiceLine, self)._compute_price()
        # TODO: deal with case of tax included in price
        self.deduction_rate = self.env['account.tax.rate']. \
            _compute_deduction_rate(
                self.industry_id, self.product_id.product_tmpl_id,
                self.invoice_id.date_invoice)
        price_tax = self.price_total - self.price_subtotal
        currency = self.currency_id or self.company_id.currency_id
        self.price_tax_d = float_round(price_tax * self.deduction_rate,
                                       currency.decimal_places)
        self.price_total_nd = self.price_total - self.price_tax_d
