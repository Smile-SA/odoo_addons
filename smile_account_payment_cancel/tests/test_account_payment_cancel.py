# -*- coding: utf-8 -*-
# (C) 2010 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests.common import TransactionCase


class AccountPaymentCancelTest(TransactionCase):

    def test_payment_cancel(self):
        """
        I create an invoice
        I validate it
        I pay it
        I check the invoice is paid
        I cancel the payment
        I check the invoice is not paid anymore
        I check the journal entries were reversed
        """
        invoice = self.env.ref('l10n_generic_coa.demo_invoice_3').copy()
        invoice.action_invoice_open()
        bank_journal = self.env['account.journal'].search(
            [('type', '=', 'bank')], limit=1)
        invoice.pay_and_reconcile(bank_journal, invoice.amount_total)
        self.assertEquals(invoice.payment_ids.mapped('state'), ['posted'])
        self.assertEquals(invoice.state, 'paid')
        today = fields.Date.today()
        invoice.payment_ids.with_context(reversal_date=today).cancel()
        self.assertEquals(invoice.payment_ids.mapped('state'), ['cancelled'])
        self.assertEquals(invoice.state, 'open')
