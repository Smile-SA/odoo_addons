# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import os.path

from odoo import fields, tools
from odoo.tests.common import SingleTransactionCase


class AccountAssetTest(SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(AccountAssetTest, cls).setUpClass()
        cls._import_demo_data()
        cls.digital_asset = cls.env.ref(
            'smile_account_asset.account_asset_asset_digitalasset0')
        cls.fixed_asset = cls.env.ref(
            'smile_account_asset.account_asset_asset_fixedasset0')
        cls.digital_category = cls.env.ref(
            'smile_account_asset.account_asset_category_digitalassets')
        cls.fixed_category = cls.env.ref(
            'smile_account_asset.account_asset_category_fixedassets')
        cls.today = fields.Date.today()

    @classmethod
    def _import_demo_data(cls):
        module = 'smile_account_asset'
        for filename in ('account_demo.xml', 'account_tax_demo.xml',
                         'account_asset_category_demo.xml',
                         'account_asset_demo.xml', 'res_company_demo.xml'):
            filepath = os.path.join(module, 'demo', filename)
            with tools.file_open(filepath) as xmlfile:
                tools.convert_xml_import(cls.env.cr, module, xmlfile=xmlfile)

    def test_010_account_asset_purchase(self):
        """
        1. I configure the company
        2. I update the vendor's expense account
        3. I confirm the purchase of the digital asset
        4. I indicate a in-service date
        5. I validate the digital asset
        6. I check the digital asset is open
        7. I post the first accounting amortization line
        8. I check the first accounting amortization line is posted
        9. I post the first fiscal amortization line
        10. I check the first fiscal amortization line is posted
        """
        self.digital_asset.company_id.write({
            'prorata_temporis': 'approched',
            'first_day_acquisition': True,
        })
        self.digital_asset.supplier_id.property_account_payable = \
            self.env['account.account'].search([
                ('code', '=', '111100'),
                ('company_id', '=', self.digital_asset.company_id.id),
            ])
        self.digital_asset.confirm_asset_purchase()
        self.digital_asset.in_service_date = self.today
        self.digital_asset.validate()
        self.assertEquals(self.digital_asset.state, 'open')
        first_accounting_depreciation_line = self.digital_asset. \
            accounting_depreciation_line_ids[0]
        first_accounting_depreciation_line.post_depreciation_line()
        self.assertEquals(first_accounting_depreciation_line.state, 'open')
        first_fiscal_depreciation_line = self.digital_asset. \
            fiscal_depreciation_line_ids[0]
        first_fiscal_depreciation_line.post_depreciation_line()
        self.assertEquals(first_fiscal_depreciation_line.state, 'open')

    def test_020_account_asset_exceptional_depreciation(self):
        """
        1. I create a exceptional depreciation line
        2. I validate the exceptional depreciation line
        3. I check the depreciation line is posted
        """
        exceptional_depreciation_line = self.digital_asset. \
            exceptional_depreciation_line_ids.create({
                'asset_id': self.digital_asset.id,
                'depreciation_value': 4000.0,
            })
        exceptional_depreciation_line.validate_exceptional_depreciation()
        self.assertTrue(exceptional_depreciation_line.is_posted)

    def test_030_account_asset_posting(self):
        """
        1. I check all journal entries linked to the digital asset are posted
        """
        moves = self.digital_asset.account_move_line_ids.mapped('move_id')
        self.assertEquals(moves.mapped('state'), ['posted'] * len(moves))

    def test_040_account_asset_accounts_change(self):
        """
        1. I change the category's asset account
        2. I check the accounts transfer
           after asset account change is effective
        3. I change the category's accounting amortization account
        4. I check the accounts transfer
           after amortization expense account change is effective
        5. I change the company's fiscal amortization account
        6. I check the accounts transfer
           after fiscal depreciation expense account change is effective
        """
        old_account = self.digital_category.asset_account_id
        new_account = self.env['account.account'].search([
            ('code', '=', 'A21'),
            ('company_id', '=', self.digital_category.company_id.id),
        ])
        self.digital_category.asset_account_id = new_account
        lines = self.digital_asset.account_move_line_ids.filtered(
            lambda line: line.account_id == old_account)
        balance = sum(lines.mapped('debit')) - sum(lines.mapped('credit'))
        self.assertTrue(tools.float_is_zero(balance, 2))
        lines = self.digital_asset.account_move_line_ids.filtered(
            lambda line: line.account_id == new_account)
        self.assertEquals(tools.float_compare(
            sum(lines.mapped('debit')),
            sum(lines.mapped('asset_id.purchase_value')), 2), 0)

        new_account = self.env['account.account'].search([
            ('code', '=', 'A281'),
            ('company_id', '=', self.digital_category.company_id.id),
        ])
        self.digital_category.accounting_depreciation_account_id = new_account
        lines = self.digital_asset.account_move_line_ids.filtered(
            lambda line: line.account_id == new_account)
        depreciation_value = self.digital_asset. \
            accounting_depreciation_line_ids[0].depreciation_value
        self.assertEquals(tools.float_compare(
            sum(lines.mapped('credit')),
            depreciation_value, 2), 0)

        new_account = self.env['account.account'].search([
            ('code', '=', 'A291'),
            ('company_id', '=', self.digital_asset.company_id.id),
        ])
        self.digital_asset.company_id.fiscal_depreciation_account_id = \
            new_account
        lines = self.digital_asset.account_move_line_ids.filtered(
            lambda line: line.account_id == new_account)
        depreciation_value = self.digital_asset. \
            fiscal_depreciation_line_ids[0].accelerated_value
        self.assertEquals(tools.float_compare(
            sum(lines.mapped('credit')),
            depreciation_value, 2), 0)

    @staticmethod
    def _save_record(new_record):
        vals = {
            field: new_record._fields[field].convert_to_write(
                new_record[field], new_record)
            for field in new_record._fields
        }
        del vals['id']
        return new_record.create(vals)

    def test_050_account_asset_history(self):
        """
        1. I change the digital asset's category
        2. I check a histroy log was created
        3. I check that the digital asset is linked to the new category
        """
        new_category = self.fixed_category
        history = self.env['account.asset.history'].new(
            {'asset_id': self.digital_asset.id})
        history._onchange_asset()
        history.category_id = new_category
        history._onchange_category()
        self._save_record(history)
        self.assertEquals(self.digital_asset.category_id, new_category)

    def test_060_account_asset_copy(self):
        """
        1. I duplicate the asset and check the copy validity
        """
        new_asset = self.digital_asset.copy()
        self.assertNotEquals(new_asset.name, self.digital_asset.name)
        self.assertTrue(new_asset.name.startswith(self.digital_asset.name))
        self.assertEquals(new_asset.state, 'draft')
        for field in ('category_id', 'asset_type', 'supplier_id',
                      'purchase_date', 'purchase_value', 'salvage_value',
                      'in_service_date', 'quantity', 'uom_id',
                      'purchase_tax_ids', 'accounting_method',
                      'accounting_annuities', 'accounting_rate',
                      'accounting_rate_visibility', 'fiscal_method',
                      'fiscal_annuities', 'fiscal_rate',
                      'fiscal_rate_visibility',
                      'benefit_accelerated_depreciation'):
            self.assertEquals(new_asset[field], self.digital_asset[field])
        for field in ('code', 'asset_history_ids', 'account_move_line_ids',
                      'invoice_line_ids', 'customer_id', 'sale_date',
                      'sale_value', 'fiscal_book_value', 'sale_result',
                      'accumulated_amortization_value', 'sale_tax_ids',
                      'sale_type', 'tax_regularization',
                      'regularization_tax_amount', 'is_out',
                      'purchase_move_id', 'purchase_cancel_move_id',
                      'sale_move_id', 'sale_cancel_move_id',
                      'purchase_account_date', 'sale_account_date',
                      'in_service_account_date'):
            self.assertFalse(new_asset[field])

    def test_070_account_asset_purchase_cancellation(self):
        """
        1. I create a new digital asset
        2. I confirm and validate this new asset
        3. I post the first depreciation lines
        4. I cancel this asset
        5. I check the digital asset is cancel
        6. I check the journal entries are reversed for this asset
        """
        new_asset = self.digital_asset.copy({'name': "Software 1"})
        new_asset.confirm_asset_purchase()
        new_asset.validate()
        new_asset.accounting_depreciation_line_ids[0].post_depreciation_line()
        new_asset.fiscal_depreciation_line_ids[0].post_depreciation_line()
        new_asset.cancel_asset_purchase()
        self.assertEquals(new_asset.state, 'cancel')
        lines = new_asset.account_move_line_ids
        balance = sum(lines.mapped('debit')) - sum(lines.mapped('credit'))
        self.assertTrue(tools.float_is_zero(balance, 2))

    def test_080_account_asset_split(self):
        """
        1. I confirm the purchase of the fixed asset
        2. I indicate a in-service date and validate the fixed asset
        3. I post the first accounting amortization line
        4. I post the first fiscal amortization line
        5. I define and validate the split of the fixed asset
        6. I check this split
        """
        self.fixed_asset.confirm_asset_purchase()
        self.fixed_asset.in_service_date = self.today
        self.fixed_asset.validate()
        self.fixed_asset.accounting_depreciation_line_ids[0]. \
            post_depreciation_line()
        self.fixed_asset.fiscal_depreciation_line_ids[0]. \
            post_depreciation_line()
        split_values = {
            'purchase_value': 20000.0,
            'salvage_value': 500.0,
            'quantity': 1.0,
        }
        fields_to_read = list(split_values.keys())
        initial_values = self.fixed_asset.read(fields_to_read)[0]
        vals = split_values.copy()
        vals['asset_id'] = self.fixed_asset.id
        wizard = self.env['account.asset.split_wizard'].create(vals)
        wizard.validate()
        new_asset = wizard.new_asset_id
        self.assertEquals(new_asset.parent_id, self.fixed_asset)
        for field in fields_to_read:
            self.assertEquals(new_asset[field], split_values[field])
            if field == 'quantity':
                self.assertEquals(new_asset[field], self.fixed_asset[field])
            else:
                self.assertEquals(
                    initial_values[field] - split_values[field],
                    self.fixed_asset[field])
        for line in self.fixed_asset.depreciation_line_ids.filtered('move_id'):
            amount_field = 'depreciation_value'
            if line.depreciation_type == 'fiscal':
                amount_field = 'accelerated_value'
            depreciation_value = sum([
                nline[amount_field]
                for nline in line.move_id.asset_depreciation_line_ids])
            self.assertEquals(tools.float_compare(
                line.move_id.amount, depreciation_value, 2), 0)

    def test_090_account_asset_modification(self):
        """
        1. I check the digital asset is open
        2. I modify the digital asset
        3. I check the modification
        """
        self.assertEquals(self.digital_asset.state, 'open')
        history = self.env['account.asset.history'].new(
            {'asset_id': self.digital_asset.id})
        history._onchange_asset()
        history.fiscal_annuities = 3
        history.note = 'Test Asset Modify'
        self._save_record(history)
        self.assertEquals(self.digital_asset.fiscal_annuities, 3)

    def test_100_account_asset_sale(self):
        """
        1. I sell the digital asset
        2. I check the digital asset is close
        3. I go out the digital asset
        4. I check the digital asset is out
        5. I check account balance (test valid only if no decomposition)
        """
        self.digital_asset.write({
            'sale_date': self.today.replace(
                year=self.today.year + 1).isoformat(),
            'sale_type': 'sale',
            'sale_value': 18000.0,
            'customer_id': self.env.ref('base.res_partner_2').id,
        })
        self.digital_asset.confirm_asset_sale()
        self.assertEquals(self.digital_asset.state, 'close')
        self.digital_asset.output()
        self.assertTrue(self.digital_asset.is_out)
        lines = self.digital_asset.account_move_line_ids
        balance = sum(lines.mapped('credit')) - sum(lines.mapped('debit'))
        result = self.digital_asset.sale_result - \
            sum(self.digital_asset.fiscal_depreciation_line_ids.
                mapped('accelerated_value'))
        self.assertEquals(tools.float_compare(result, balance, 2), 0)

    def test_110_account_asset_sale_cancellation(self):
        """
        1. I cancel the sale of the digital asset
        2. I check the digital asset is open
        3. I check the sale infos are empty
        4. I check depreciation board is ok
        """
        self.digital_asset.cancel_asset_sale()
        self.assertEquals(self.digital_asset.state, 'open')
        for field in ('sale_date', 'sale_value', 'sale_type', 'customer_id'):
            self.assertFalse(self.digital_asset[field])
        depreciation_end_date = max(self.digital_asset.depreciation_line_ids.
                                    mapped('depreciation_date'))
        annuities = self.digital_asset.accounting_annuities
        if self.today.strftime('%m-%d') == '01-01' or \
                self.digital_asset.exceptional_depreciation_line_ids:
            annuities -= 1
        end_date = self.today.replace(
            year=self.today.year + annuities, month=12, day=31)
        self.assertEquals(depreciation_end_date, end_date)

    def test_120_account_asset_scrapping(self):
        """
        1. I scrap the digital asset
        2. I check the digital asset is close
        3. I go out the digital asset
        4. I check the book value is null
        """
        self.digital_asset.write({
            'sale_date': self.today.replace(
                year=self.today.year + 1).isoformat(),
            'sale_type': 'scrapping',
        })
        self.digital_asset.confirm_asset_sale()
        self.assertEquals(self.digital_asset.state, 'close')
        self.digital_asset.output()
        self.assertTrue(
            not self.digital_asset.company_id.convert_book_value_if_scrapping
            or not self.digital_asset.book_value)

    def test_130_account_asset_auto_creation(self):
        """
        1. I indicate a asset category to the demo invoice lines
        2. I force set asset_creation='auto' for the fixed category
        3. I validate the demo invoice
        """
        invoice = self.env.ref('l10n_generic_coa.demo_invoice_0')
        invoice.invoice_line_ids[0].asset_category_id = self.digital_category
        invoice.invoice_line_ids[1].asset_category_id = self.fixed_category
        self.fixed_category.asset_creation = 'auto'
        invoice.action_invoice_open()
        self.assertTrue(bool(invoice.invoice_line_ids[1].asset_id))

    def test_140_account_asset_inventory(self):
        """
        1. I create and post inventory lines for current fiscalyear
        """
        self.digital_asset.company_id.create_inventory_entries()

    def test_150_account_asset_special(self):
        """
        1. I post depreciation lines for current period
        """
        self.digital_asset.company_id.post_depreciation_lines()

    def test_160_account_asset_special(self):
        """
        1. I update the vendor's expense account
        2. I confirm the purchase of the second digital asset
        3. I validate the second digital asset
        4. I check the second digital asset is open
        5. I post the first accounting amortization line
        6. I post the first fiscal amortization line
        """
        digital_asset = self.env.ref(
            'smile_account_asset.account_asset_asset_digitalasset1')
        self.env.ref('base.res_partner_1').property_account_payable = \
            self.env['account.account'].search([
                ('code', '=', '111100'),
                ('company_id', '=', digital_asset.company_id.id),
            ])
        digital_asset.confirm_asset_purchase()
        digital_asset.validate()
        self.assertEquals(digital_asset.state, 'open')
        digital_asset.accounting_depreciation_line_ids[0]. \
            post_depreciation_line()
        digital_asset.fiscal_depreciation_line_ids[0]. \
            post_depreciation_line()
