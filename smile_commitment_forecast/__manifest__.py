# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Budget Commitment Forecast",
    "version": "0.1",
    "depends": [
        "smile_commitment_base",
    ],
    "author": "Smile",
    "license": 'LGPL-3',
    "description": """
Features

    * Allow to follow commitment & available forecast per budget line

Suggestions & Feedback to: Corentin Pouhet-Brunerie
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Accounting & Finance',
    "sequence": 20,
    "data": [
        "security/security.xml",
        "views/account_analytic_view.xml",
        "views/account_budget_view.xml",
    ],
    "demo": [],
    "auto_install": False,
    "installable": True,
    "application": False,
}
