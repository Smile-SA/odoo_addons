# -*- coding: utf-8 -*-
# (C) 2010 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Smile Base",
    "version": "0.2.3",
    "depends": [
        'fetchmail',
        'web_editor',
        'web_planner',
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """""",
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        "security/base_security.xml",
        "security/res_users.yml",
        "data/act_actions_window.yml",
        "data/ir_lang.yml",
        "data/im_odoo_support.yml",
        "data/ir_module_menu.yml",
        "data/warning_data.xml",
        "views/ir_actions_view.xml",
        "views/template.xml",
    ],
    "qweb": [
        "static/src/xml/base.xml",
        "static/src/xml/env_ribbon.xml",
    ],
    "auto_install": True,
    "installable": True,
    "application": False,
}
