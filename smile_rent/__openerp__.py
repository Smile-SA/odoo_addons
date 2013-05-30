# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name": "Rental Management",
    "version": "0.1",
    "depends": ["procurement"],
    "author": "Smile",
    "description": """
    TODO:
     * Manage rental order lines adding after validation
     * Manage product availabilities
     * Manage product packagings
     * Split rental order lines at pickings splitting
     * Allow to select production lot in rental order line and manage picking chages
    """,
    "summary": "Rental Orders",
    "website": "http://www.smile.fr",
    "category": 'Sales Management',
    "sequence": 20,
    "init_xml": [
        "security/rent_security.xml",
        "security/ir.model.access.csv",
        "data/sequence_data.xml",
        "data/mail_data.xml",
    ],
    "update_xml": [
        "workflow/rental_workflow.xml",
        "view/company_view.xml",
        "view/product_view.xml",
        "view/rent_view.xml",
    ],
    'demo_xml': [],
    'test': [],
    "auto_install": False,
    "installable": True,
    "application": True,
}
