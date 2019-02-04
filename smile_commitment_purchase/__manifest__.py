# -*- coding: utf-8 -*-
# (C) 2014 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Purchase Commitment",
    "version": "0.1",
    "depends": [
        "purchase",
        "smile_commitment_base",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
This module generates analytic lines at purchase confirmation / cancellation.
You can follow-up purchase commitment per budget line.

Usage

    * Define a budgetary position listening to general accounts.
    * Define a budget with budgetary position and analytic account.
    * Commitment amount is 0.
    * Purchase a product on the selected account, associate the analytic account on the purchase line.
    * Confirm the purchase.
    * Return to your budget to see the new commitment amount.

Suggestions & Feedback to: Corentin Pouhet-Brunerie &
Isabelle RICHARD
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Purchase Management',
    "sequence": 20,
    "data": [
            "views/res_config_settings_view.xml"
    ],
    "auto_install": True,
    "installable": True,
    "application": False,
}
