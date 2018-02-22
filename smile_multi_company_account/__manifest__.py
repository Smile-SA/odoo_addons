# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Multi-company - Invoicing",
    "version": "0.1",
    "depends": [
        "smile_multi_company_base",
        "account",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Multi-company Invoicing
=======================

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Hidden',
    "sequence": 20,
    "data": [
        'views/res_company_view.xml',
    ],
    "qweb": [],
    "auto_install": True,
    "installable": True,
    "application": False,
}
