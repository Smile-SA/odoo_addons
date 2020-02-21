# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Access Control",
    "version": "1.0",
    "author": "Smile",
    "license": 'LGPL-3',
    "category": "Tools",
    "description": "",
    "depends": ['base'],
    "data": [
        "views/res_users_view.xml",
        "data/res_users_data.xml",
        "views/res_groups_view.xml",
        'views/res_company_view.xml',
    ],
    "demo": [],
    "installable": True,
    "active": False,
    "uninstall_hook": "uninstall_hook",
}
