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
    "name": "Unit of Measure Conversion",
    "version": "0.1",
    "depends": ["purchase"],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
This module allows to convert UoMs via a conversion table, by product, between reference units of each category

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "website": "http://www.smile.fr",
    'category': 'Sales Management',
    "sequence": 19,
    "data": [
        "security/ir.model.access.csv",
        "views/product_view.xml",
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
