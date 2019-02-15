# -*- coding: utf-8 -*-
# (C) 2013 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Database Upgrade",
    "version": "0.2",
    "depends": ["web"],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """""",
    "summary": "",
    "website": "http://www.smile.fr",
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
