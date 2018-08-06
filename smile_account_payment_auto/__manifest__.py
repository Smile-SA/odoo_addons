# -*- coding: utf-8 -*-
# (C) 2013 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Auto pay suppliers at due date",
    "version": "0.1",
    "license": 'AGPL-3',
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
