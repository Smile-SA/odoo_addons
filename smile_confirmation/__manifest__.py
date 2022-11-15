# -*- coding: utf-8 -*-
# (C) 2021 Smile (<https://www.smile.eu>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Confirm/Alert pop-up before saving",
    "version": "0.1",
    "depends": ['base','web'],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
    """,
    "summary": "",
    "website": "https://www.smile.eu",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        'security/ir.model.access.csv',
        'views/popup_message.xml',
    ],

    'assets': {
        'web.assets_backend': [
            "smile_confirmation/static/src/js/smile_confirmation.js",
        ]
    },

    "auto_install": False,
    "installable": True,
    "application": False,
}
