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
    "name": "@api.depends filtering",
    "version": "0.1",
    "depends": ["smile_filtered_from_domain"],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
@api.depends filtering
======================

This module allows to filter records to recompute by specifying a domain for a trigger.

Example:
    @api.depends(('product_id.lst_price', [('invoice_id.state', '=', 'draft')]))

To work, this module must be defined as a wide module.

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
