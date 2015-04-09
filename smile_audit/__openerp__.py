# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "Audit Trail",
    "version": "0.1",
    "sequence": 100,
    "category": "Tools",
    "author": "Smile",
    "license": 'AGPL-3',
    "website": 'http://www.smile.fr',
    "description": """
This module lets administrator track every user operation on all the objects of the system (for the moment, only create, write and unlink methods).

WARNING: This module is not compatible with audit, so uninstall it before installing this one.

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "depends": [
        'base',
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/audit_rule_view.xml',
        'views/audit_log_view.xml',
    ],
    "test": [
        'test/audit_test.yml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
