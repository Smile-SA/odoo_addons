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
    "name": "Server Actions R* Trigger Rules Engine (aka Sartre)",
    "version": "6.0",
    "sequence": 100,
    'complexity': "expert",
    "category": "Tools",
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "description": """
Concept

* Give to functional users the possibility to create trigger rules for server actions
* Make easier to technical users the application maintenance and scalability

Principle

A rule applies to a single object and is composed of:
1. Triggers on
    * object creation
    * object update
    * object deletion
    * object date (creation date, last update date or another date)
    * object function field recalculation (thus you can trigger the calculation of function fields on cascade)
    * object methods (with an argument named self, cr, uid, ids in its signature)
2. Filters
    * operators: you can create your own operators (which apply to current or old field value)
    * value age: current or old values if the rule trigger is the object update
3. Actions
    * all server action types: email (native or with poweremail), sms, object creation/update, etc
    * run each action once per instance or once for all instances

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "depends": ['smile_log'],
    "init_xml": [
        'security/sartre_security.xml',
        'security/ir.model.access.csv',
        'data/sartre_sequence.xml',
        'data/ir_cron_data.xml',
        'data/sartre_data.xml',
    ],
    "update_xml": [
        'view/ir.xml',
        'view/sartre_view.xml',
    ],
    "demo_xml": [
        'demo/sartre_demo.xml',
    ],
    "test": [
        'test/sartre_test.yml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
