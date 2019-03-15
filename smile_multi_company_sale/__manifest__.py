# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Multi-company - Sales",
    "version": "0.3",
    "depends": [
        "smile_multi_company_account",
        "sale_management",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """""",
    "summary": "",
    "website": "",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        'views/sale_order_view.xml',
        'wizard/sale_make_invoice_advance_views.xml',
    ],
    "qweb": [],
    "auto_install": True,
    "installable": True,
    "application": False,
}
