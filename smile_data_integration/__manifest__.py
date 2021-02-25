# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Odoo Data Integration",
    "version": "0.1",
    "depends": [
        "base",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Features:
* Add old_id field in models, except from _old_id = False
* Accept external_id as create / write values or write / unlink ids
  or search domain operands

Execution:
* odoo.py -c <config_file> -d <db_name> --load=web,smile_data_integration


Suggestions & Feedback to: Corentin Pouhet-Brunerie
    & Stéphane Salah
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "data": [],
    "qweb": [],
    "auto_install": True,
    "installable": True,
    "application": False,
}
