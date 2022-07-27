# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Smile Base",
    "version": "0.2.3",
    "depends": [
        'mail',
        'web_editor',
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """""",
    "summary": "",
    "website": "",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        "security/base_security.xml",
        "security/res_users.xml",
        "data/warning_data.xml",
        "views/ir_actions_view.xml",
        "views/template.xml",
        "views/ir_actions_server_view.xml",
    ],
    "qweb": [
        "static/src/xml/base.xml",
    ],
    "pre_init_hook": 'pre_init_hook',
    "post_init_hook": 'post_init_hook',
    "auto_install": True,
    "installable": True,
    "application": False,
}
