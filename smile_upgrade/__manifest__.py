# -*- coding: utf-8 -*-
# (C) 2019 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Database Upgrade",
    "version": "14.0.1.0.0",
    "depends": ["web"],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": "",
    "summary": "",
    "website": "",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        "views/webclient_templates.xml",
    ],
    "qweb": [
        "static/src/xml/code_version.xml",
    ],
    "auto_install": True,
    "installable": True,
    "application": False,
}
