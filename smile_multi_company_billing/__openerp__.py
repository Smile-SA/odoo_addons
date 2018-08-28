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
    "name": "Smile Multi-company Billing",
    "version": "0.1",
    "author": "Smile",
    "website": "http://www.smile.fr",
    "category": 'Generic Modules/Accounting',
    "depends": ["smile_multi_company_account"],
    "description": """Inter-company Billing

At the validation of an invoice / credit note,
if the billed partner is a company referenced in the current database,
the system create automatically a document for this second company from the original one:
* customer invoice -> supplier invoice
* supplier invoice -> customer invoice
* customer credit note -> supplier credit note
* supplier credit note -> customer credit note

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "init_xml": [],
    "update_xml": [
        'view/res_company_view.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
