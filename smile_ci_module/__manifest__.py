# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Modules Repository",
    "version": "0.1",
    "depends": [
        "smile_ci",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Modules repository
==================

Features

    # List installed branch modules at each stable/unstable build

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr &
antoine.fouille@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        'security/ir.model.access.csv',
        'security/scm_security.xml',
        'data/scm.version.csv',
        'views/scm_version_view.xml',
        'views/scm_repository_branch_module_view.xml',
        'views/scm_repository_branch_view.xml',
        'views/scm_menu.xml',
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
