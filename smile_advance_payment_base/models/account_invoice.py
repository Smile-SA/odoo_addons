# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    recovery_ids = fields.One2many(
        'account.payment.recovery', 'invoice_id',
        'Advance payments', readonly=True,
        states={'draft': [('readonly', False)]})

    @api.multi
    def action_move_create(self):
        """ Create recevories at invoice validation.
        """
        res = super(AccountInvoice, self).action_move_create()
        self._recover_advance_payments()
        return res

    @api.one
    def _recover_advance_payments(self):
        residual = self.residual_company_signed
        for advance_payment in self._get_advance_payments():
            if residual and advance_payment.advance_residual:
                advance_residual = advance_payment.advance_residual
                if advance_payment.currency_id != self.currency_id:
                    advance_residual = advance_payment.currency_id. \
                        with_context(date=self.invoice_id.date_invoice). \
                        compute(advance_residual, self.currency_id)
                amount = min(residual, advance_residual)
                recovery = self.env['account.payment.recovery'].create({
                    'invoice_id': self.id,
                    'payment_id': advance_payment.id,
                    'amount': amount,
                })
                recovery.post()
                residual -= amount

    @api.multi
    def _get_advance_payments(self):
        # Override in smile_advance_payment_purchase
        return self.env['account.payment'].browse()

    @api.multi
    def action_invoice_cancel(self):
        """ Reverse recoveries when invoice is cancelled.
        """
        res = super(AccountInvoice, self).action_invoice_cancel()
        self.recovery_ids.mapped('move_id').reverse_moves()
        return res
