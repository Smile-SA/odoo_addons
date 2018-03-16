# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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
    "name": "filtered_from_domain",
    "version": "0.1",
    "depends": ["base"],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
This module allows to filter records from a search domain.

Example:
    records.filtered_from_domain([('state', '=', 'draft'), ('line_ids.product_id.name', '=', 'My product')])

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "website": "http://www.smile.fr",
    'category': 'Tools',
    "sequence": 0,
    "data": [],
    "auto_install": True,
    "installable": True,
    "application": False,
}
