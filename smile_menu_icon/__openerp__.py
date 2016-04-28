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
    "name": "Smile Menu Icon",
    "version": "0.2",
    "depends": ['mail'],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Feature
    * Add Font-Awesome icon in menu.

How-to add icon next to a menu title
    1. Go to the Font-Awesome website, select your icon (e.g.: 'fa fa-eye')
    2. Go to Settings > Technical > User Interface > Menu Items
    3. Select the menu you want to add / change the icon
    4. Paste the fa code (e.g.: 'fa fa-eye') in fa ico
    5. And... voilà !

    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        "views/template.xml",
        "views/edit_menu_access.xml",
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}