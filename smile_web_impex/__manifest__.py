# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Access rules for Import/Export",
    "version": "0.1",
    "depends": ['web'],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Add access rules for import / export features
=============================================

For each user, you can indicate if it can export / import data

Suggestions & Feedback to: Corentin Pouhet-Brunerie
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        'security/web_impex_security.xml',
        'views/webclient_templates.xml',
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
