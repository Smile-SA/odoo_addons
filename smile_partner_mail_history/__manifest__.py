# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Smile Partner Mail History",
    "version": "13.0.1",
    "depends": [
        "mail",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": "Consult Received Emails From Partner Form",
    "summary": "",
    "website": "",
    "category": "Discuss",
    "data": [
        # Security
        # Data
        # Reports
        # Views
        'views/mail_message_views.xml',
        'views/partner_mail_history.xml',
        'views/res_partner_views.xml',
        # Wizard
    ],
    "demo": [
    ],
    "qweb": [
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
