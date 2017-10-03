# -*- coding: utf-8 -*-

from odoo.tests.common import SingleTransactionCase


class DiscountContractForecastTest(SingleTransactionCase):

    def setUp(self):
        super(DiscountContractForecastTest, self).setUp()
        self.contract = self.env.ref(
            'smile_discount_contract.discount_contract_demo')

    def test_000_compute_theoretical_values(self):
        """
            1. One after the other, I test the forecast methods
               by specifying it on a discount contract
               and computing theoretical values
            2. I check no exception was raised
        """
        ForecastMethod = self.env['discount.contract.forecast_method']
        for forecast_method in ForecastMethod.search([]):
            self.contract.forecast_method_id = forecast_method
            self.contract.compute_discount_amount()
