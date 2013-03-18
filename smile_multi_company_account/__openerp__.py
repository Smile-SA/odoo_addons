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
    "name": "Smile Multi-company Accounting",
    "version": "0.1",
    "author": "Smile",
    "website": "http://www.smile.fr",
    "category": 'Generic Modules/Accounting',
    "depends": ["account", "smile_account_fiscal_position_journal", "smile_multi_company_base"],
    "description": """Override Invoice.action_move_create method to manage multi-company application

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "init_xml": [
        'security/multi_company_security.xml',
    ],
    "update_xml": [
        'view/invoice_view.xml',
        'view/account_view.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
