# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Supplier Advance Payments",
    "version": "0.1",
    "license": 'AGPL-3',
    "depends": [
        "purchase",
        "smile_advance_payment_base",
    ],
    "author": "Smile",
    "description": """Supplier Advance Payments Management

Suggestions & Feedback to: Corentin Pouhet-Brunerie
    """,
    "website": "http://www.smile.fr",
    "category": "Accounting & Finance",
    "sequence": 32,
    "data": [
        "views/account_payment_view.xml",
        "views/purchase_order_view.xml",
    ],
    "demo": [],
    'test': [],
    "auto_install": False,
    "installable": True,
    "application": False,
}
