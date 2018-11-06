# -*- coding: utf-8 -*-
# (C) 2013 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Application period for taxes",
    "version": "0.1",
    "license": 'AGPL-3',
    "depends": ["account"],
    "author": "Smile",
    "description": """Manage application period for taxes

Suggestions & Feedback to: Corentin Pouhet-Brunerie
    """,
    "website": "http://www.smile.fr",
    "category": 'Accounting & Finance',
    "sequence": 32,
    "data": [
        "views/account_tax_view.xml",
        "views/account_tax_template_view.xml",
        "wizard/account_invoice_tax_wizard_view.xml",
    ],
    "demo": [],
    'test': [],
    "auto_install": False,
    "installable": True,
    "application": False,
}
