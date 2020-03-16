# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Smile Anonymize Partner",
    "version": "0.0.1",
    "depends": ['base'],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Smile Anonymize Partner:
------------------------
This module anonymize the personal data of partners .\n
Use:\n
- To change fields to anonymized you should surcharge
method get_anonymize_fields() that return a dictionary
with 3 keys: fields, phones and emails with a list of fields for each.\n
    Default values: {
        'fields': ['name', 'street', 'street2', 'comment'],
        'phones': ['phone', 'mobile'],
        'emails': ['email']
    }\n
- To anonymize personal data of your partners you should call action:
action_anonymization(). This method display a popup with a warning
that this action is irreversible and the Yes/Cancel buttons.\n
- When record is anonymized the boolean is_anonymized get as value True.\n
    """,
    "summary": "",
    "website": "",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        'security/smile_anonymize_partner_security.xml',
        'views/res_partner_views.xml',
        'wizard/confirm_anonymization_view.xml',
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
