# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Smile Purge Data",
    "version": "20.0.1.0.0",
    "depends": ['base'],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        'security/ir.access.csv',
        'views/purge_data_views.xml',
    ],
    "auto_install": False,
    "images": ["static/description/banner.gif"],
    "installable": True,
    "application": False,
}
