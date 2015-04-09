# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>). All Rights Reserved
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
    'name': 'Warehouse Management: Waves',
    'version': '1.0',
    "author": "Smile",
    "website": 'http://www.smile.fr',
    'category': 'Stock Management',
    "license": 'AGPL-3',
    'summary': 'Wave Type, Cancellation Propagation',
    "description": """
Features

    * Add picking wave types
    * Make configurable the propagation of cancellation between pickings, waves and stock moves

Todo

    * Complete stock picking and stock picking wave views

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "depends": ['stock_picking_wave'],
    "data": [
        'security/ir.model.access.csv',
        'security/stock_picking_wave_security.xml',
        'views/stock_view.xml',
    ],
    "installable": True,
    "active": False,
}
