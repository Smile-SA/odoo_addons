# (C) 2023 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Display Decimal Precision",
    "version": "14.0.0.0.1",
    "depends": ["web","account"],
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
