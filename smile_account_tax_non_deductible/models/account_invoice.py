# -*- coding: utf-8 -*-
# (C) 2013 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def write(self, vals):
        res = super(AccountInvoice, self).write(vals)
        self._adjust_non_deductible_amounts()
        return res

    @api.one
    def _adjust_non_deductible_amounts(self):
        if self.invoice_line_ids:
            amount_total = \
                sum(self.invoice_line_ids.mapped('price_total_nd')) + \
                sum(self.invoice_line_ids.mapped('price_tax_d'))
            if amount_total != self.amount_total:
                self.invoice_line_ids[-1].price_total_nd -= \
                    amount_total - self.amount_total
            amount_tax = sum(self.invoice_line_ids.mapped('price_tax_d'))
            if self.tax_line_ids:
                amount_tax2 = \
                    sum(self.tax_line_ids.mapped('amount_deductible'))
                if amount_tax != amount_tax2:
                    self.tax_line_ids[-1].amount_deductible -= \
                        amount_tax2 - amount_tax

    @api.multi
    def invoice_line_move_line_get(self):
        res = super(AccountInvoice, self).invoice_line_move_line_get()
        for vals in res:
            invoice_line = self.env['account.invoice.line']. \
                browse(vals['invl_id'])
            vals['price'] = invoice_line.price_total_nd
        return res

    @api.multi
    def tax_line_move_line_get(self):
        res = super(AccountInvoice, self).tax_line_move_line_get()
        for vals in res:
            invoice_tax = self.env['account.invoice.tax']. \
                browse(vals['invoice_tax_line_id'])
            vals['price'] = invoice_tax.amount_deductible
        return res

    def _prepare_tax_line_vals(self, line, tax):
        vals = super(AccountInvoice, self)._prepare_tax_line_vals(line, tax)
        vals['deduction_rate'] = line.deduction_rate
        return vals
