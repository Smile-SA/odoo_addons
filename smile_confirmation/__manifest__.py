# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Confirm/Alert pop-up before saving",
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
        'views/assets.xml',
        'views/popup_message.xml',
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
