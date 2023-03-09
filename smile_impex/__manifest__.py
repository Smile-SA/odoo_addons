# -*- coding: utf-8 -*-
# (C) 2020 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Import / Export",
    "version": "15.0.1.0.0",
    "depends": ['smile_log'],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Import / Export

Features

    # Define an import/export template by
        * choose a model
        * define a method to import/export records
        * define a domain to filter lines to export
    # Create actions to generate a new import/export
        * a client action to generate an export on the fly from records list
        * a scheduled action to generate periodically a new import/export
    # Log execution exceptions

Suggestions & Feedback to: Corentin Pouhet-Brunerie
& Isabelle Richard
    """,
    "summary": "",
    "website": "https://www.smile.eu",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        'security/ir.model.access.csv',
        'views/export_view.xml',
        'views/import_view.xml',
        'views/menu_view.xml',
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
