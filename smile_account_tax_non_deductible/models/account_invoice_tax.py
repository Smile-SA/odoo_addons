# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.float_utils import float_round
from odoo.addons.account.models.account_invoice import _logger


class AccountInvoiceTax(models.Model):
    _inherit = 'account.invoice.tax'

    deduction_rate = fields.Float(
        digits=(13, 12))
    amount_deductible = fields.Monetary(
        compute='_compute_amount_total')

    @api.one
    @api.depends('amount', 'amount_rounding', 'deduction_rate')
    def _compute_amount_total(self):
        super(AccountInvoiceTax, self)._compute_amount_total()
        currency = self.invoice_id.currency_id or \
            self.invoice_id.company_id.currency_id
        self.amount_deductible = float_round(
            self.amount_total * self.deduction_rate, currency.decimal_places)

    @api.depends('invoice_id.invoice_line_ids')
    def _compute_base_amount(self):
        tax_grouped = {}
        for invoice in self.mapped('invoice_id'):
            tax_grouped[invoice.id] = invoice.get_taxes_values()
        for tax in self:
            tax.base = 0.0
            if tax.tax_id:
                key = tax.tax_id.get_grouping_key({
                    'tax_id': tax.tax_id.id,
                    'account_id': tax.account_id.id,
                    'account_analytic_id': tax.account_analytic_id.id,
                    # Added by Smile #
                    'deduction_rate': tax.deduction_rate,
                    ##################
                })
                if tax.invoice_id and key in tax_grouped[tax.invoice_id.id]:
                    tax.base = tax_grouped[tax.invoice_id.id][key]['base']
                else:
                    _logger.warning(
                        'Tax Base Amount not computable probably due to a '
                        'change in an underlying tax (%s).', tax.tax_id.name)
