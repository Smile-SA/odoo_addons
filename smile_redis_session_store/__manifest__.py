# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Redis Session Store",
    "version": "0.1",
    "depends": ["base"],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """Use Redis Session instead of File system

    Suggestions & Feedback to: Isabelle Richard
    """,
    "summary": "",
    "website": "",
    "category": 'Tools',
    "auto_install": False,
    "installable": True,
    "application": False,
    "external_dependencies": {
        'python': ['redis'],
    },
}
