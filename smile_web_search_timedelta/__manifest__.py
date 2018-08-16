# -*- coding: utf-8 -*-
# (C) 2015 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Search in timedelta",
    "version": "0.1",
    "depends": ['web'],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Allows to search in timedelta
=============================

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        'views/webclient_templates.xml',
    ],
    "qweb": [
        'static/src/xml/base.xml',
    ],
    "auto_install": True,
    "installable": True,
    "application": False,
}
