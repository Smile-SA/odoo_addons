# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name": "Pricelist Versions",
    "version": "0.1",
    "license": 'AGPL-3',
    "depends": [
        "product",
    ],
    "author": "Smile",
    "description": """
Pricelist Versions
==================

Suggestions & Feedback to: mounir.salim@smile-maroc.com & corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": "Sales",
    "sequence": 20,
    "data": [
        "security/ir.model.access.csv",
        "security/pricelist_security.xml",
        "views/pricelist_view.xml",
    ],
    'demo': [],
    'test': [],
    "auto_install": False,
    "installable": True,
    "application": False,
}
