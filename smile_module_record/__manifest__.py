# -*- coding: utf-8 -*-
# (C) 2011 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Export Customizations as a Module",
    "version": "0.1",
    "depends": ["base"],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
    This module aims to export data in a new module containing CSV/XML files.

    This module built and test on Odoo.

    Features
        * Export data in CSV or XML through a new module compatible
            with import (i.e. data files are ordered and splitted if necessary)
        * Export automatically properties linked to selected models

    TODO
        * Manage workflow - Eg.: export a validated invoice and import it
            at this same state, in particular if account moves were exported

    Suggestions & Feedback to: Corentin Pouhet-Brunerie
    """,
    "website": "",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        "wizard/base_module_export_view.xml",
        "wizard/base_module_import_view.xml",
    ],
    'demo': [],
    'test': [],
    "auto_install": False,
    "installable": True,
    "application": False,
}
