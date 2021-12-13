# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Checkbook Management",
    "version": "13.0.1.0.0",
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "license": 'AGPL-3',
    "category": "Accounting",
    "description": """
Generate and follow checkbooks
------------------------------

You can create checkbook by:

* specify a range of numbers
* specify a quantity and a start number

Manually follow your checks by updating status:

* Available
* Used
* Lost
* Destroyed
* Stolen

Suggestions & Feedback to: Isabelle RICHARD
""",
    "depends": ['web'],
    "data": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/account_check_view.xml',
        'views/template.xml',
        'wizard/account_checkbook_wizard_view.xml',
    ],
    "demo": [],
    "installable": True,
    'post_init_hook': 'account_checkbook_wizard',
    "active": False,
}
