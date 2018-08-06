# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.addons.account.tests.account_test_classes import AccountingTestCase


class TestAdvancePayment(AccountingTestCase):

    def setUp(self):
        super(TestAdvancePayment, self).setUp()
        self.partner = self.env.ref('base.res_partner_1')
        self.partner.property_account_payable_advance_id = \
            self.partner.property_account_payable_id
        self.product = self.env.ref('product.product_product_8')
        self.product.purchase_method = 'purchase'

    def test_advance_payment_on_purchase_order(self):
        """
        I create a purchase order
        I confirm it
        I create and post an advance payment
        I create a supplier invoice
        I validate it
        I check advance payment was recovered
        """
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'name': self.product,
                'product_id': self.product.id,
                'product_qty': 5.0,
                'product_uom': self.product.uom_po_id.id,
                'price_unit': 500.0,
                'date_planned': fields.Datetime.now(),
            })]
        })
        purchase_order.button_confirm()
        bank_journal = self.env['account.journal'].search(
            [('type', '=', 'bank')], limit=1)
        bank_journal.is_advance_payment = True
        payment_method = bank_journal.outbound_payment_method_ids[0]
        advance_payment = self.env['account.payment'].create({
            'is_advance_payment': True,
            'partner_id': self.partner.id,
            'purchase_id': purchase_order.id,
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'journal_id': bank_journal.id,
            'payment_method_id': payment_method.id,
            'amount': 500.0,
        })
        advance_payment.post()
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'purchase_id': purchase_order.id,
            'account_id': self.partner.property_account_payable_id.id,
            'type': 'in_invoice',
        })
        invoice.purchase_order_change()
        invoice.action_invoice_open()
        self.assertEquals(len(invoice.payment_ids), 1)
        self.assertEquals(
            invoice.residual,
            purchase_order.amount_total - advance_payment.amount)
