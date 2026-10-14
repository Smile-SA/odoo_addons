# (C) 2025 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestIrHttp(TransactionCase):

    def setUp(self):
        super().setUp()
        self.currency_model = self.env['res.currency']

    def test_06_get_currencies(self):
        """
            Test currency information in get_all_currencies method.

            Prerequisites:
                - Create a test currency with display_rounding=0.001
            Test:
                - Call get_all_currencies on res.currency
                - Check if the created currency is in the returned dictionary
                - Verify the digits precision value
            Expected:
                - The created currency should be in the returned currencies
                - The digit precision should be 3 (from display_rounding)
        """

        currency = self.currency_model.create({
            'name': 'Test Currency',
            'symbol': 'T€',
            'rounding': 0.01,
            'decimal_places': 2,
            'display_rounding': 0.001,
        })
        currencies = self.currency_model.get_all_currencies()
        self.assertIn(currency.id, currencies)
        self.assertEqual(currencies[currency.id]['digits'][1], 3)
