# -*- coding: utf-8 -*-
# (C) 2013 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.tools.float_utils import float_round


class AccountTaxNonDeductibleTest(TransactionCase):

    def test_account_tax_non_deductible(self):
        """
        I configure taxation rates on activity sectors
        I create an invoice
        I check if non deductible amount is correct
        I validate the invoice
        I check if journal entry takes into account the non deductible amount
        """
        deduction_rate = 0.8
        industry = self.env.ref('base.res_partner_industry_A')
        self.env['account.tax.rate'].create({
            'rate_type': 'taxation',
            'start_date': '2018-01-01',
            'value': deduction_rate,
            'industry_id': industry.id,
        })
        invoice = self.env.ref(
            'l10n_generic_coa.demo_invoice_equipment_purchase').copy()
        invoice.invoice_line_ids.write({'industry_id': industry.id})
        currency = invoice.currency_id or invoice.company_id.currency_id
        for line in invoice.invoice_line_ids:
            price_tax = line.price_total - line.price_subtotal
            price_tax_d = float_round(price_tax * deduction_rate,
                                      currency.decimal_places)
            self.assertEquals(line.price_tax_d, price_tax_d)
        invoice.action_invoice_open()
        self.assertTrue(invoice.amount_total in
                        invoice.move_id.line_ids.mapped('credit'))
        self.assertTrue(price_tax_d in
                        invoice.move_id.line_ids.mapped('debit'))
