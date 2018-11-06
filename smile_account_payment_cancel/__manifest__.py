# -*- coding: utf-8 -*-
# (C) 2010 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Smile Payment Cancellation Management",
    "version": "0.1",
    "license": 'AGPL-3',
    "depends": ["account_cancel"],
    "category": "Generic Modules/Accounting",
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "description": """Payment Cancellation Management

    Instead of deleting account move when you cancel a payment,
    this module reserves it if this journal entry was validated,
    removes it otherwise.
    
    Suggestions & Feedback to: Corentin Pouhet-Brunerie
    """,
    "depends": [
        'account',
    ],
    "data": [
        "wizard/account_payment_reversal_view.xml",
    ],
    "demo": [],
    "installable": True,
    "active": False,
}
