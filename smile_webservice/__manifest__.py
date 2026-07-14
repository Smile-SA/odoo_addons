# -*- coding: utf-8 -*-
# (C) 2025 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Smile WebService",
    "version": "19.0.1.0.0",
    "depends": ['web'],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """Add a view to visualize webservice calls from the
interface, with input and output values, and replay error calls
    """,
    "images": ["static/description/banner.gif"],
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
