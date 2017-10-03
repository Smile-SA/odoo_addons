# -*- coding: utf-8 -*-

from odoo.tests.common import SingleTransactionCase


class DiscountContractTest(SingleTransactionCase):

    def setUp(self):
        super(DiscountContractTest, self).setUp()
        self.contract = self.env.ref(
            'smile_discount_contract.discount_contract_demo')
        self.contract.contract_line_ids.unlink()

    def test_000_create_contract_lines(self):
        """
            1. I compute the discount amount
            2. I check if lines were created
            3. I check if there are as many lines as rules
        """
        self.contract.compute_discount_amount()
        self.assertTrue(self.contract.contract_line_ids)
        self.assertEquals(len(self.contract.contract_line_ids),
                          len(self.contract.contract_tmpl_id.rule_ids))

    def test_010_validate_contract(self):
        """
            1. I validate the discount contract
            2. I check if the discount contract is validated
        """
        self.contract.set_open()
        self.assertEquals(self.contract.state, 'open')

    def test_020_duplicate_contract(self):
        """
            1. I duplicate the discount contract
            2. I check if a new draft contract was created
        """
        new_contract = self.contract.copy()
        self.assertEquals(new_contract.state, 'draft')

    def test_030_cancel_contract(self):
        """
            1. I cancel the new discount contract
            2. I check if a new contract is cancelled
        """
        new_contract = self.contract.copy()
        new_contract.set_cancel()
        self.assertEquals(new_contract.state, 'cancel')

    def test_040_close_contract(self):
        """
            1. I specify a close reason
            2. I close the discount contract
            2. I check if the discount contract is closed
        """
        CloseReason = self.env['discount.contract.close_reason']
        self.contract.close_reason_id = CloseReason.search([], limit=1)
        self.contract.set_close()
        self.assertEquals(self.contract.state, 'close')
