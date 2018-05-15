# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name": "Auto pay suppliers at due date",
    "version": "0.1",
    "depends": ["account"],
    "author": "Smile",
    "description": """Auto pay suppliers

1. Define payment mode on suppliers
    * individual: invoice by one
    * grouped: all invoices with a same due date
2. Indicate invoices to pay
3. A scheduled action, generate payments at due date

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "website": "http://www.smile.fr",
    "category": "Accounting & Finance",
    "sequence": 32,
    "data": [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/account_invoice_view.xml',
        'views/account_payment_method_view.xml',
        'views/account_payment_view.xml',
        'views/res_partner_view.xml',
    ],
    "demo": [],
    'test': [],
    "auto_install": False,
    "installable": True,
    "application": False,
}
