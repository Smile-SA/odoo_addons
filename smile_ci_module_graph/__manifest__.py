# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Modules Graph",
    "version": "0.1",
    "depends": [
        "smile_ci_module",
        "smile_widgets_extension",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Modules repository
==================

Features

    # Generate a graph of installed modules at each build

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        'views/scm_repository_branch_module_view.xml',
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
