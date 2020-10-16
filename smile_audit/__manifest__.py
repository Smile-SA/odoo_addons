# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Audit Trail",
    "version": "0.1",
    "sequence": 100,
    "category": "Tools",
    "author": "Smile",
    "license": 'LGPL-3',
    "description": """
This module lets administrator track every user operation on
all the objects of the system
(for the moment, only create, write and unlink methods).
    """,
    "depends": [
        'base',
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/audit_rule_view.xml',
        'views/audit_log_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
