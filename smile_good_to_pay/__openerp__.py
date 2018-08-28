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
    'name': 'Smile good to pay',
    'version': '1.0',
    'depends': [
        'account',
        'account_voucher',
        'purchase',
        'stock_account',
    ],
    'author': 'Smile',
    'description': """
            # Smile good to pay
    """,
    'summary': '',
    'website': 'http://www.smile.fr',
    'category': 'Account',
    'sequence': 10,
    'data': [
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'views/account_invoice_view.xml',
        'views/purchase_view.xml',
        'views/stock_view.xml',
        'views/res_users_view.xml',
        'views/procurement_view.xml',
        'views/rejection_cause_view.xml',
        'views/wizard_invoice_rejection_cause_view.xml',
    ],
    'demo_xml': [],
    'test': [],
    'auto_install': False,
    'installable': True,
    'application': False,
}
