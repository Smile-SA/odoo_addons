# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Display Decimal Precision",
    "version": "0.3",
    "depends": ["decimal_precision"],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
This module allows to distinguish computation digits
and display digits in decimal precision.
""",
    "website": "",
    "category": "Hidden/Dependency",
    "sequence": 32,
    "data": [
        "views/decimal_precision_view.xml",
        "views/res_currency_view.xml",
    ],
    "auto_install": True,
    "installable": True,
    "application": False,
}
