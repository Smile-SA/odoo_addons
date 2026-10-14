# (C) 2025 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestResCurrency(TransactionCase):

    def setUp(self):
        super().setUp()
        self.currency_model = self.env['res.currency']

    def test_07_display_decimal_places_no_display_rounding(self):
        """
            Test display_decimal_places when display_rounding is zero.

            Prerequisites:
                - Create a currency with decimal_places=2
                and display_rounding=0

            Test:
                - Check the computed display_decimal_places value

            Expected:
                - display_decimal_places should equal decimal_places (2)
        """
        currency = self.currency_model.create({
            'name': 'Test Currency',
            'symbol': 'T€',
            'rounding': 0.01,
            'decimal_places': 2,
            'display_rounding': 0,
        })
        self.assertEqual(currency.display_decimal_places, 2)

    def test_08_display_decimal_places_with_display_rounding(self):
        """
            Test display_decimal_places with smaller display_rounding.
            Prerequisites:
                - Create a currency with decimal_places=2 and
                display_rounding=0.001
            Test:
                - Check the computed display_decimal_places value
            Expected:
                - display_decimal_places should be 3
                (from display_rounding precision)
        """
        currency = self.currency_model.create({
            'name': 'Test Currency',
            'symbol': 'T€',
            'rounding': 0.01,
            'decimal_places': 2,
            'display_rounding': 0.001,
        })
        self.assertEqual(currency.display_decimal_places, 3)

    def test_09_display_decimal_places_with_large_display_rounding(self):
        """
            Test display_decimal_places with larger display_rounding.
            Prerequisites:
                - Create a currency with decimal_places=2 and
                display_rounding=1
            Test:
                - Check the computed display_decimal_places value
            Expected:
                - display_decimal_places should be 0 (integer precision)
        """
        currency = self.currency_model.create({
            'name': 'Test Currency',
            'symbol': 'T€',
            'rounding': 0.01,
            'decimal_places': 2,
            'display_rounding': 1,
        })
        self.assertEqual(currency.display_decimal_places, 0)
