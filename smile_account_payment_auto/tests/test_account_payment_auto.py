# -*- coding: utf-8 -*-

from odoo import fields
from odoo.tests.common import TransactionCase


class AccountPaymentAutoTest(TransactionCase):

    def setUp(self):
        super(AccountPaymentAutoTest, self).setUp()
        self.payment_method = self.env.ref(
            'account.account_payment_method_manual_out')
        self.payment_method.partner_bank_required = True
        self.payment_method.bank_journal_ids = \
            self.env['account.journal'].search([('type', '=', 'bank')])
        self.partner = self.env.ref('base.res_partner_1')
        self.partner.payment_mode = 'G'
        self.partner.payment_method_id = self.payment_method

    def _create_invoice(self, **kwargs):
        product = self.env.ref('stock.product_icecream')
        account = self.env['account.invoice.line'].get_invoice_line_account(
            kwargs.get('type') or 'in_invoice', product,
            False, self.env.user.company_id)
        invoice_date = fields.Date.today()
        invoice_date = str(int(invoice_date[:4]) - 1) + invoice_date[4:]
        vals = {
            'partner_id': self.partner.id,
            'partner_bank_id': self.partner.bank_ids and
            self.partner.bank_ids[0].id,
            'payment_term_id': self.env.ref(
                'account.account_payment_term').id,
            'type': 'in_invoice',
            'date_invoice': invoice_date,
            'invoice_line_ids': [(0, 0, {
                'name': product.name,
                'product_id': product.id,
                'account_id': account.id,
                'price_unit': 10.0,
                'quantity': 5.0,
            })]
        }
        vals.update(kwargs)
        return self.env['account.invoice'].create(vals)

    def test_generate_payments(self):
        """
        I create 2 invoices and 1 refund for a partner in grouped payment mode
        I pay them at due due
        I launch payments generation
        I check if only one payment was created for these 3 invoices
        """
        invoices = self._create_invoice()
        invoices |= self._create_invoice()
        invoices |= self._create_invoice(type='in_refund')
        invoices.action_invoice_open()
        invoices.set_to_progress_paid()
        payments = invoices.generate_payments()
        self.assertEquals(len(payments), 1)
        self.assertEquals(payments.amount, 50.0)
