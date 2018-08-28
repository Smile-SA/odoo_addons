# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Smile Payment Method',
    'version': '1.0',
    'depends': ["base",
                "stock",
                "sale",
                "purchase",
                "account",
                ],
    'author': 'Smile',
    'description': """
            # Smile Payment Method
    """,
    'summary': '',
    'website': 'http://www.smile.fr',
    'category': 'Account',
    'sequence': 10,
    'data': [
        'data/account_payment_method_data.xml',
        'security/ir.model.access.csv',
        'views/res_partner_view.xml',
        'views/account_payment_method_view.xml',
        'views/account_view.xml',
        'views/purchase_view.xml',
        'views/sale_view.xml',
        'views/stock_view.xml',
    ],
    'test': [],
    'auto_install': False,
    'installable': True,
    'application': False,
}
