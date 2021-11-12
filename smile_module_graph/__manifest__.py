# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Modules Graph",
    "version": "15.0.1.0.0",
    "depends": ["base"],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """""",
    "website": "http://www.smile.eu",
    "category": "Hidden",
    "sequence": 32,
    "data": [
        'security/ir.model.access.csv',
        "wizard/ir_module_graph_wizard_view.xml",
        "views/module_view.xml",
    ],
    "demo": [],
    'test': [],
    "auto_install": False,
    "installable": True,
    "application": False,
    'external_dependencies': {
        'python': ['pydot'],
    }
}
