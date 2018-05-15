# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountPaymentReversal(models.TransientModel):
    _name = 'account.payment.reversal'
    _description = 'Account Payment Reversal'

    reversal_date = fields.Date(
        'Date of reversals', required=True, default=fields.Date.today,
        help="Enter the date of the reversal journal entries.")

    @api.multi
    def reverse_payment(self):
        self.ensure_one()
        payment_ids = self._context.get('payment_ids')
        payments = self.env['account.payment'].browse(payment_ids)
        payments.with_context(reversal_date=self.reversal_date).cancel()
        return {'type': 'ir.actions.act_window_close'}
