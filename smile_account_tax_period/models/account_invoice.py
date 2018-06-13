# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import format_date


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_open(self):
        if not self._context.get('force_invoice_open'):
            invoices_in_error, errors = self._check_unvalid_taxes()
            if invoices_in_error:
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Unvalid taxes'),
                    'res_model': 'account.invoice.tax.wizard',
                    'view_mode': 'form',
                    'view_id': False,
                    'res_id': False,
                    'context': {
                        'default_invoices_in_error':
                            repr(invoices_in_error.ids),
                        'default_errors': '\n'.join(errors),
                    },
                    'target': 'new',
                }
        return super(AccountInvoice, self).action_invoice_open()

    @api.multi
    def _check_unvalid_taxes(self):
        invoices_in_error, errors = self.browse(), []
        for invoice in self:
            date_invoice = invoice.date_invoice or fields.Date.today()
            for tax in invoice.mapped('invoice_line_ids.invoice_line_tax_ids'):
                if tax.date_start and date_invoice < tax.date_start:
                    invoices_in_error |= invoice
                    errors.append(
                        _('The tax %s shall apply from %s') %
                        (tax.name, format_date(self.env, tax.date_start)))
                if tax.date_stop and date_invoice > tax.date_stop:
                    invoices_in_error |= invoice
                    errors.append(
                        _('The tax %s shall apply to %s') %
                        (tax.name, format_date(self.env, tax.date_stop)))
        return invoices_in_error, errors
