# (C) 2020 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Multiple Emails / Phone numbers",
    "version": "20.0.1.0.0",
    "sequence": 100,
    "category": "Tools",
    "author": "Smile",
    "license": 'LGPL-3',
    "website": 'https://smile.eu/fr',
    "images": ['static/description/banner.gif'],
    "description": """
Add multiple emails / phone numbers per contact

    """,
    "depends": [
        "contacts",
        "phone_validation",
    ],
    "data": [
        "security/ir.access.csv",
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
