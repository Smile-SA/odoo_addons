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

from num2words import num2words

# Tools to display amounts and percentages in French format,
# as numeric or in letters


def split_integer_and_decimal(number):
    if type(number) in (str, int):
        number = float(number)
    number = round(number, 2)
    return int(number), round(number * 100 % 100)


def display_number_fr(number, with_decimal=True):
    "12394.029 will be displayed as 12 394,03"
    number_format = '{0:,.2f}' if with_decimal else '{0:,}'
    return number_format.format(number).replace(',', ' ').replace('.', ',')


def format_amount_fr(amount, currency_symbol, currency_in_letters, in_letters=False):
    """
    Formats amounts with currency (conversion in letters is optional).

    @param amount: the amount to format
    @param currency_symbol: unicode, € for example
    @param currency_in_letters: unicode, euros for example
    @param in_letters: bool, True if the amount must be written in letters
    @return unicode, the formated amount
    """
    if not in_letters:
        return u"%s %s" % (display_number_fr(amount), currency_symbol)
    if type(amount) == int or int(amount) == amount:
        return u"%s %s" % (num2words(amount, lang='fr'), currency_in_letters or currency_symbol)
    integer, decimal = split_integer_and_decimal(amount)
    return u"%s %s et %s %s" % (
        num2words(integer, lang='fr'),
        currency_in_letters or currency_symbol,
        num2words(decimal, lang='fr'),
        'centimes',
    )


def format_percentage_fr(percentage, in_letters=False):
    """
    Formats percentages (conversion in letters is optional).

    @param percentage: the percentage to format
    @return unicode, the formated percentage
    """
    if not in_letters:
        return u"%s%%" % display_number_fr(percentage)
    if type(percentage) == int or int(percentage) == percentage:
        return u"%s pour cent" % num2words(percentage, lang='fr')
    integer, decimal = split_integer_and_decimal(percentage)
    return u"%s %s %s pour cent" % (
        num2words(integer, lang='fr'),
        'virgule',
        num2words(decimal, lang='fr'),
    )
