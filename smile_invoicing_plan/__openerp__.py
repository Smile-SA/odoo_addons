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
    "name": "Invoicing Plan for Sales",
    "version": "1.0",
    "category": "Generic Modules/Sales & Purchases",
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "description": """Invoicing Plan for Sales

Suggestions & Feedback to: samir.rachedi@smile.fr & corentin.pouhet-brunerie@smile.fr
""",
    "depends": ['sale', 'account'],
    "init_xml": ['ir_cron_data.xml'],
    "update_xml": [
        'sale_view.xml',
        'product_view.xml',
        'invoicing_plan_view.xml',
        'invoicing_plan_wizard.xml',
        'wizard/change_commitment.xml',
        'security/invoicing_plan_security.xml',
        'security/ir.model.access.csv',
    ],
    "test": ['test/account_invoicing_plan.yml',
             ],
    "demo_xml": [],
    "installable": True,
    "active": False,
    "certificate": '',
}
