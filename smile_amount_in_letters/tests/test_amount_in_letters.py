# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.tests.common import TransactionCase
from openerp.addons.smile_amount_in_letters.tools import format_amount_fr, format_percentage_fr


class TestAmountInLetters(TransactionCase):

    def setUp(self):
        super(TestAmountInLetters, self).setUp()
        self.currency_symbol = u'€'
        self.currency_in_letters = u'euros'

    def test_amount_with_currency(self):
        amount = 1029.392
        res = format_amount_fr(amount, self.currency_symbol, self.currency_in_letters, in_letters=False)
        self.assertEquals(u'1 029,39 €', res, 'Amount was not correctly formated')

    def test_amount_without_decimal_with_currency(self):
        amount = 1029
        res = format_amount_fr(amount, self.currency_symbol, self.currency_in_letters, in_letters=False)
        self.assertEquals(u'1 029,00 €', res, 'Amount was not correctly formated')

    def test_amount_with_currency_in_letters(self):
        amount = 1029.392
        res = format_amount_fr(amount, self.currency_symbol, self.currency_in_letters, in_letters=True)
        self.assertEquals(u'mille vingt-neuf euros et trente-neuf centimes', res, 'Amount was not correctly formated')

    def test_amount_in_letters_with_decimal_lower_than_10(self):
        amount = 25.08
        res = format_amount_fr(amount, self.currency_symbol, self.currency_in_letters, in_letters=True)
        self.assertEquals(u'vingt-cinq euros et huit centimes', res, 'Amount was not correctly formated')

    def test_amount_without_decimal_with_currency_in_letters(self):
        amount = 1029
        res = format_amount_fr(amount, self.currency_symbol, self.currency_in_letters, in_letters=True)
        self.assertEquals(u'mille vingt-neuf euros', res, 'Amount was not correctly formated')

    def test_percentage(self):
        percentage = 52.39
        res = format_percentage_fr(percentage, in_letters=False)
        self.assertEquals(u'52,39%', res, 'Percentage was not correctly formated')

    def test_percentage_without_decimal(self):
        percentage = 52
        res = format_percentage_fr(percentage, in_letters=False)
        self.assertEquals(u'52,00%', res, 'Percentage was not correctly formated')

    def test_percentage_without_decimal_lower_than_10(self):
        percentage = 52.03
        res = format_percentage_fr(percentage, in_letters=False)
        self.assertEquals(u'52,03%', res, 'Percentage was not correctly formated')

    def test_percentage_without_decimal_greather_than_10(self):
        percentage = 52.3
        res = format_percentage_fr(percentage, in_letters=False)
        self.assertEquals(u'52,30%', res, 'Percentage was not correctly formated')

    def test_percentage_in_letters(self):
        percentage = 52.39
        res = format_percentage_fr(percentage, in_letters=True)
        self.assertEquals(u'cinquante-deux virgule trente-neuf pour cent', res, 'Percentage was not correctly formated')

    def test_percentage_without_decimal_in_letters(self):
        percentage = 52
        res = format_percentage_fr(percentage, in_letters=True)
        self.assertEquals(u'cinquante-deux pour cent', res, 'Percentage was not correctly formated')

    def test_percentage_with_decimal_greater_than_10(self):
        percentage = 8.5
        res = format_percentage_fr(percentage, in_letters=True)
        self.assertEquals(u'huit virgule cinquante pour cent', res, 'Percentage was not correctly formated')

    def test_percentage_with_decimal_lower_than_10(self):
        percentage = 8.05
        res = format_percentage_fr(percentage, in_letters=True)
        self.assertEquals(u'huit virgule cinq pour cent', res, 'Percentage was not correctly formated')
