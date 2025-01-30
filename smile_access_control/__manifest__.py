# -*- coding: utf-8 -*-
# (C) 2022 Smile (<https://www.smile.eu>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Access Control",
    "version": "17.0.1.0.0",
    "author": "Smile",
    "license": 'LGPL-3',
    "category": "Tools",
    "description": "This module allows to manage users' rights using profiles.",
    "depends": ['base', 'auth_signup'],
    "data": [
        "data/res_users_data.xml",
        "views/res_users_view.xml",
        "views/res_groups_view.xml",
        'views/res_company_view.xml',
    ],
    "demo": [],
    "installable": True,
    "active": True,
    "uninstall_hook": "uninstall_hook",
}
