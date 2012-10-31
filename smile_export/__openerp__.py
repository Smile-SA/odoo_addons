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
    "name": "Export",
    "version": "1.0",
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "category": "Tools",
    "description": """Export whatever objects

Principle

* Define an export template
    * choose a object
    * define a domain to filter lines to export
    * indicate if a line can be export only once or several times
* Create actions to generate a new export
    * a client action to generate a export in fly
    * a scheduled action to generate periodically a new export
* Log execution exceptions

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
""",
    "depends": ['smile_log'],
    "init_xml": [],
    "update_xml": [
        'security/smile_export_security.xml',
        'security/ir.model.access.csv',
        'export_view.xml',
    ],
    "demo_xml": [],
    "installable": True,
    "active": False,
}
