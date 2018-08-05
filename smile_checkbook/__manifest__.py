# -*- encoding: utf-8 -*-
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Checkbook Management",
    "version": "1.0",
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "license": 'LGPL-3',
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

Suggestions & Feedback to: isabelle.richard@smile.fr
""",
    "depends": ['account'],
    "data": [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/account_check_view.xml',
        'views/template.xml',
        'wizard/account_checkbook_wizard_view.xml',
    ],
    "demo": [
        'demo/account_check.yml',
    ],
    "installable": True,
    "active": False,
}
