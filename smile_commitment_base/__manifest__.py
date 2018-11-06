# -*- coding: utf-8 -*-
# (C) 2014 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Budget Commitment",
    "version": "0.1",
    "depends": [
        "account_budget",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Features

    * Allow to follow-up commitment per budget line
    * Define commitment limit per budget position and per user

Todo

    * Add tolerance percentage or fixed amount for over budget commitment

Suggestions & Feedback to: Corentin Pouhet-Brunerie &
Isabelle RICHARD
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Accounting & Finance',
    "sequence": 20,
    "data": [
        "security/ir.model.access.csv",
        "views/account_budget_view.xml",
        "views/account_analytic_view.xml",
        "views/res_users_view.xml",
    ],
    "demo": [
        "demo/account_budget_demo.xml",
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
