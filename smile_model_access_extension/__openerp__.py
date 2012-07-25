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
    "name": "Model Access Extension",
    "version": "1.0",
    'category': 'Generic Modules/Base',
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "description": """
This module allows to make readonly some fields (all by default) of an object in function of:
* object states (all by default)
* connected user groups (all by default)

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
""",
    "depends": ['base'],
    "init_xml": [
        'security/ir.model.access.csv',
    ],
    "update_xml": [
        'ir.xml',
    ],
    "demo_xml": [],
    "installable": True,
    "active": False,
    "certificate": '',
}
