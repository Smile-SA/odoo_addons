# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Multiple Emails / Phone numbers",
    "version": "14.0.1.0.0",
    "sequence": 100,
    "category": "Tools",
    "author": "Smile",
    "license": 'LGPL-3',
    "website": 'http://www.smile.fr',
    "description": """
Add multiple emails / phone numbers per contact

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "depends": [
        "contacts",
        "phone_validation",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/res_partner_contact_point_tag_data.xml",
        "views/res_partner_contact_point_tag_views.xml",
        "views/res_partner_contact_point_views.xml",
        "views/res_partner_views.xml",
        "views/menus.xml",
    ],
    "demo": [],
    'installable': True,
    'auto_install': True,
    'application': False,
}
