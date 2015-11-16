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

{
    'name': "Smile - Amount in letters",
    'summary':
    """
        Write an amount in letters
    """,
    'description':
    """
        This module allows you to print an amount in letters with the currency.
    """,
    'author': "Smile",
    'category': 'Accounting & Finance',
    'version': '0.1',

    'data': [
        # Data
        'data/res_currency_before_data.yml',
        'data/res.currency.csv',
        'data/res_currency_after_data.yml',
        # Views
        'views/res_currency_view.xml',
    ],
    'external_dependencies': {
        'python': ['num2words'],
    }
}
