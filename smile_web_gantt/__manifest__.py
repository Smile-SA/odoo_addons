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
    "name": "Web Gantt",
    "version": "0.1",
    "category": "Hidden",
    "depends": [
        "web_gantt",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Web Gantt Extension
===================

* Allow to display weeks of year

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "website": "http://www.smile.fr",
    "sequence": 0,
    "data": [
        "views/webclient_templates.xml",
    ],
    "demo": [],
    "auto_install": True,
    "installable": True,
    "application": False,
}
