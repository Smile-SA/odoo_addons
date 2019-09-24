# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestBIC(TransactionCase):
    def setUp(self):
        super(TestBIC, self).setUp()
        self.Bank = self.env['res.bank']
        self.bank = self.Bank.create({
            'name': 'Test Bank',
        })

    def test_create_with_wrong_bic(self):
        """
            Create a bank with wrong bic
        """
        with self.assertRaises(ValidationError):
            self.Bank.create({
                'name': 'Test Bank wrong bic',
                'bic': 'its a wrong bic number',
            })

    def test_create_with_good_bic(self):
        """
            Create a bank with grood bic
        """
        self.Bank.create({
            'name': 'Test Bank wrong bic',
            'bic': 'AAAAAAAA',
        })

    def test_write_good_bic(self):
        """
            Write a bank with good bic
        """
        self.bank.write({
            'bic': 'AAAAAAAA',
        })

    def test_write_wrong_bic(self):
        """
            Write a bank with good bic
        """
        with self.assertRaises(ValidationError):
            self.bank.write({
                'bic': 'its a wrong bic number',
            })

    def test_remove_bic(self):
        """
            Write a bank with empty bic
        """
        with self.assertRaises(ValidationError):
            self.bank.write({
                'bic': None,
            })


class TestBICRegEx(TransactionCase):
    def setUp(self):
        super(TestBICRegEx, self).setUp()
        self.Bank = self.env['res.bank']
        self.bank = self.Bank.create({
            'name': 'Test Bank',
        })

    def test_only_letters_ok(self):
        """
            test only letters
        """
        self.bank.write({
            'bic': 'AAAAAAAA',
        })

    def test_with_numbers_ok(self):
        """
            test with numbers
        """
        self.bank.write({
            'bic': 'AAAAAA99',
        })

    def test_with_endgroup_ok(self):
        """
            test with numbers
        """
        self.bank.write({
            'bic': 'AAAAAA99FFF',
        })

    def test_lowerletters_nok(self):
        """
            test with lower
        """
        with self.assertRaises(ValidationError):
            self.bank.write({
                'bic': 'zzzzAAAA',
            })

    def test_numbers_nok(self):
        """
            test with lower
        """
        with self.assertRaises(ValidationError):
            self.bank.write({
                'bic': '1AAAAAAA',
            })

    def test_endgroup_nok(self):
        """
            test with lower
        """
        with self.assertRaises(ValidationError):
            self.bank.write({
                'bic': 'AAAAAAAAsss',
            })
