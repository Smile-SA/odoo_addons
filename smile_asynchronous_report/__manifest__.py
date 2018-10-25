
# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Asynchronous Report",
    "version": "0.1",
    "sequence": 100,
    "category": "Tools",
    "author": "Smile",
    "license": 'AGPL-3',
    "website": 'http://www.smile.fr',
    "description": """
Features

    * Allows to launch report generation in background
    * Notify users from instant messaging

Suggestions & Feedback to: Corentin Pouhet-Brunerie
    """,
    "depends": [
        "mail",
    ],
    "data": [
        "views/ir_actions_report.xml",
    ],
    'installable': True,
    'auto_install': True,
    'application': False,
}
