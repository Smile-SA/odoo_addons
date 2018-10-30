# -*- coding: utf-8 -*-
# (C) 2017 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Multi-company - Invoicing",
    "version": "0.1",
    "depends": [
        "smile_multi_company_base",
        "account",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """""",
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Hidden',
    "sequence": 20,
    "data": [
        'views/res_company_view.xml',
    ],
    "qweb": [],
    "auto_install": True,
    "installable": True,
    "application": False,
}
