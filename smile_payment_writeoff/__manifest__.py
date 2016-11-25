# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name": "Payment_writeoff amount",
    "version": "0.1",
    "sequence": 100,
    "category": "Accounting & Finance",
    "author": "Smile",
    "license": 'AGPL-3',
    "website": 'http://www.smile.fr',
    "description": """
Payment_writeoff amount auto paid
=================================

This module add fields, on company, loss and profit amounts and accounts.
When a payment is done from invoice, if writeoff is in the allowed amount, mark invoice as fully paid with the profit/loss account.


Suggestions & Feedback to: matthieu.joossen@smile.fr
    """,
    "depends": ["account_voucher"],
    "data": [
        'views/res_company_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
