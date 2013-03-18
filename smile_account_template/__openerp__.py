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
    "name": "Smile Account Template",
    "version": "0.1",
    "author": "Smile",
    "website": "http://www.smile.fr",
    "category": "Generic Modules/Accounting",
    "depends": ["account_accountant"],
    "description": """Account Template

This module allows to :
    * configure account journal templates
    * indicate reserve profit & loss account
    * link account templates and products

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "init_xml": [
        'security/ir.model.access.csv',
    ],
    "update_xml": [
        'view/account_view.xml',
        'view/ir_sequence_view.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
}
