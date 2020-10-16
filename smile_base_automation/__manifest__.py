# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Automated Actions",
    "version": "0.1",
    "depends": [
        "base_automation",
        "smile_log",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """""",
    "summary": "",
    "website": "",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron_data.xml",
        "views/ir_actions.xml",
        "views/ir_model_methods_view.xml",
        "views/base_automation_view.xml",
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
