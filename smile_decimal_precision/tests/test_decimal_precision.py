# (C) 2025 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestDecimalPrecision(TransactionCase):

    def setUp(self):
        super().setUp()
        self.dp_model = self.env['decimal.precision']

    def test_01_create_decimal_precision(self):
        """
            Test creation of decimal precision with display_digits.
            Prerequisites:
                - Access to decimal.precision model
            Test:
                - Create decimal precision with display_digits=3
            Expected:
                - The created record should have display_digits=3
        """
        dp = self.dp_model.create({
            'name': 'Test Precision',
            'digits': 4,
            'display_digits': 3
        })
        self.assertEqual(dp.display_digits, 3)

    def test_02_display_precision_get(self):
        """
            Test display_precision_get method with existing precision.
            Prerequisites:
                - Create decimal precision with display_digits=3
            Test:
                - Call display_precision_get with the created precision name
            Expected:
                - Method should return 3 (the display_digits value)
        """
        self.dp_model.create({
            'name': 'Test Precision',
            'digits': 4,
            'display_digits': 3
        })
        result = self.dp_model.display_precision_get('Test Precision')
        self.assertEqual(result, 3)

    def test_03_display_precision_get_default(self):
        """
            Test display_precision_get method with non-existent precision.
            Prerequisites:
                - No precision with the name 'Non Existent'
            Test:
                - Call display_precision_get with a non-existent precision name
            Expected:
                - Method should return default value 2
        """
        result = self.dp_model.display_precision_get('Non Existent')
        self.assertEqual(result, 2)

    def test_04_get_display_precision(self):
        """
            Test get_display_precision method with existing precision.
            Prerequisites:
                - Create decimal precision with display_digits=3
            Test:
                - Call get_display_precision with the created precision name
            Expected:
                - Method should return tuple (16, 3)
        """
        self.dp_model.create({
            'name': 'Test Precision',
            'digits': 4,
            'display_digits': 3
        })
        result = self.dp_model.get_display_precision(self.env,
                                                     'Test Precision')
        self.assertEqual(result, (16, 3))

    def test_05_get_display_precision_default(self):
        """
            Test get_display_precision method with non-existent precision.
            Prerequisites:
                - No precision with the name 'Non Existent'
            Test:
                - Call get_display_precision with a non-existent precision name
            Expected:
                - Method should return default tuple (16, 2)
        """
        result = self.dp_model.get_display_precision(self.env, 'Non Existent')
        self.assertEqual(result, (16, 2))
