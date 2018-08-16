# -*- coding: utf-8 -*-
# (C) 2015 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Hidden',
    "sequence": 20,
    "data": [
        'security/web_impex_security.xml',
        'views/webclient_templates.xml',
    ],
    "auto_install": True,
    "installable": True,
    "application": False,
}
