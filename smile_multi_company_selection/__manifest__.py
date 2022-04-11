# -*- coding: utf-8 -*-
# (C) 2022 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Smile Multi Company Selection",
    "version": "1.0",
    "depends": [
        'web',
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Smile Multi Company Selection
=============================

This module allows you to choose companies from the dropdown company menu,
the page will not be reloaded until the user click on validate button.
""",
    "summary": "",
    "website": "http://www.smile.fr",
    "category": "Company",
    "data": [
        'views/webclient_templates.xml',
    ],
    "qweb": [
        'static/src/xml/switch_company_menu.xml',
    ],
    "images": ['static/description/select_compagnies.png'],
    "auto_install": False,
    "installable": True,
    "application": False,
}
