# -*- coding: utf-8 -*-
# (C) 2025 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Smile Partner Mail History",
    "version": "20.0.1.0.0",
    "depends": [
        "web",
        "mail",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": "Consult Received Emails From Partner Form",
    "summary": "",
    "website": "",
    "category": "Discuss",
    "data": [
        'views/mail_message_views.xml',
        'views/res_partner_views.xml',
    ],
    "assets": {
        "web.assets_backend": [
            'smile_partner_mail_history/static/src/scss/partner_mail_history.scss',  # noqa 501
        ],
    },
    "images": ["static/description/banner.gif"],
    "auto_install": False,
    "installable": True,
    "application": True,
}
