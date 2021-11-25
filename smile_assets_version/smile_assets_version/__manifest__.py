# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Smile Assets Version",
    "version": "0.1",
    "sequence": 100,
    "category": "Tools",
    "author": "Smile",
    "license": 'AGPL-3',
    "website": 'http://www.smile.fr',
    "description": """
This module replace checksum on files assets by checksum based on
code_version of smile_upgrade when server.environment == prod
    """,
    "depends": [
        'website',
        'smile_upgrade',
    ],
    "data": [],
    'installable': True,
    'auto_install': True,
    'application': False,
}
