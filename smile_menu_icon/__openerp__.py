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
    "version": "0.3",
    "depends": ['mail'],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Features
    * Add Font-Awesome icon in menu (or submenu).
    * Add Font-Awesome icon in page/tab of a Form View.

How-to add icon next to a menu title
    1. Go to the Font-Awesome website, select your icon (e.g.: 'fa-eye')
    2. Go to Settings > Technical > User Interface > Menu Items
    3. Select the menu you want to add / change the icon
    4. Paste the fa code (e.g.: 'fa-eye') in Font Awesome Icon
    5. And... voilà !

How-to add icon next to a menu title in page/tab of a Form View
    1. Go to the Font-Awesome website, select your icon (e.g.: 'fa-eye')
    2. In your form view add icon attribute on page element (e.g. : '<page string="Information" icon="fa-eye">'
    3. And... voilà !

TODO : Old API => New API

    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        "views/template.xml",
        "views/edit_menu_access.xml",
    ],
    "qweb": [
        "static/src/xml/base.xml",
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
