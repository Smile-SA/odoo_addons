# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Purchase without product",
    "version": "0.1",
    "depends": ["purchase"],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """Make product not required on a purchase order line

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "website": "http://www.smile.fr",
    "category": "Purchases",
    "sequence": 32,
    "data": [
        "views/purchase_order_view.xml",
    ],
    "demo": [],
    'test': [],
    "auto_install": False,
    "installable": True,
    "application": False,
}
