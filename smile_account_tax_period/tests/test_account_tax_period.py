# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class AccountTaxPeriodTest(TransactionCase):

    def test_account_tax_period(self):
        """
        I configure a tax with a end date
        I create an invoice
        I check if a wizard is open
        I force invoices validation
        I check if the invoice is validated
        """
        invoice = self.env.ref(
            'l10n_generic_coa.demo_invoice_equipment_purchase').copy()
        invoice.mapped('invoice_line_ids.invoice_line_tax_ids').write(
            {'date_stop': '208-01-01'})
        action = invoice.action_invoice_open()
        self.assertTrue(isinstance(action, dict))
        vals = {
            key.replace('default_', ''): value
            for key, value in action.get('context').items()
            if key.startswith('default_')
        }
        wizard = self.env['account.invoice.tax.wizard'].create(vals)
        wizard.force_invoice_open()
        self.assertEquals(invoice.state, 'open')
