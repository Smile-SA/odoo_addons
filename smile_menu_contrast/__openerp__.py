# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "Contrasted Menu",
    "version": "0.1",
    "depends": ['mail'],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Feature
    * Change the color of the links in the main menu. (Add contrast)

    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        "views/template.xml",
    ],
    "auto_install": True,
    "installable": True,
    "application": False,
}
