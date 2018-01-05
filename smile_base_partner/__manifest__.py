# -*- encoding: utf-8 -*-
##############################################################################
#
#    odoo, Open Source Management Solution
#    Copyright (C) 2017 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name": "Partner Organisation",
    "version": "0.1",
    "depends": [
        "sales_team",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Partner Organisation
=====================

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "website": "http://www.smile.fr",
    'category': 'Organisation',
    "sequence": 0,
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_view.xml",
        "views/res_partner_type_view.xml",
        "data/res_partner_type_data.xml",
    ],
    "demo": [],
    "auto_install": True,
    "installable": True,
    "application": False,
}
