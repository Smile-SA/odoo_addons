# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class AccountInvoiceTaxWizard(models.TransientModel):
    _name = 'account.invoice.tax.wizard'
    _description = 'Unvalid Taxes Wizard'
    _rec_name = 'errors'

    invoices_in_error = fields.Text(required=True)
    errors = fields.Text(required=True)

    @api.multi
    def force_invoice_open(self):
        self = self.with_context(force_invoice_open=True)
        for wizard in self:
            ids = safe_eval(wizard.invoices_in_error)
            invoices = self.env['account.invoice'].browse(ids)
            invoices.action_invoice_open()
        return {'type': 'ir.actions.act_window_close'}
