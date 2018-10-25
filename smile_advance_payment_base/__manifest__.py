# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Advance Payments - Base",
    "version": "0.1",
    "license": 'AGPL-3',
    "depends": ["account"],
    "author": "Smile",
    "description": """Supplier Advance Payments Management

Suggestions & Feedback to: Corentin Pouhet-Brunerie
    """,
    "website": "http://www.smile.fr",
    "category": "Accounting & Finance",
    "sequence": 32,
    "data": [
        "security/ir.model.access.csv",
        "views/account_journal_view.xml",
        "views/account_payment_view.xml",
        "views/res_partner_view.xml",
    ],
    "demo": [],
    'test': [],
    "auto_install": False,
    "installable": True,
    "application": False,
}
