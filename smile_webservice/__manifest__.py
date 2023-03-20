# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Smile WebService",
    "version": "0.1",
    "depends": ['web'],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        'security/ir.model.access.csv',
        'views/webservice_call_view.xml',
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
    'external_dependencies': {
        'python': ['requests', 'xmltodict'],
    }
}
