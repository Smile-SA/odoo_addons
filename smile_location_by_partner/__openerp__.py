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
    "name": "Smile Location by partner",
    "version": "0.1",
    "depends": ["stock"],
    "author": "Smile",
    "description": """
    * Create  2 stock_location by partner :
        - [in] + partner.name
        - [out] + partner.name
    * The prefix can be changed in the configuration tab of the company.
Suggestions & Feedback to: messaoud.guerrida@smile.fr, bruno.joliveau@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Stock Management',
    "sequence": 20,
    "init_xml": [

    ],
    "update_xml": [
                   "view/company_view.xml",
    ],
    'demo_xml': [],
    'test': [],
    "auto_install": False,
    "installable": True,
    "application": True,
}
