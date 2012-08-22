# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "Smile Analytic Multi-Axis",
    "version": "0.2",
    "author": "Smile",
    "website": "http://www.smile.fr",
    "category": "Generic Modules/Accounting",
    "depends": ["account_accountant"],
    "description": """Multi-Axis Analytic Accounting

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "init_xml": [
        'security/ir.model.access.csv',
        'data/analytic_sequence.xml',
    ],
    "update_xml": [
        'analytic_view.xml',
        'wizard/analytic_wizard_view.xml',
    ],
    'demo_xml': [
#        'demo/analytic_multiaxis_demo.yml',
    ],
    'test': [
#        'test/analytic_multiaxis_test.yml',
    ],
    'installable': True,
    'active': False,
}
