# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name": "Login as another user in website",
    "version": "0.1",
    "author": "Smile",
    "website": 'http://www.smile.fr',
    "license": 'AGPL-3',
    "category": "Tools",
    "description": """
Allows to login as another user in website
For example, this option could be useful to check what's displayed
for your customers.
==========================================

Suggestions & Feedback to: Corentin Pouhet-Brunerie & Victor Bahl
""",
    "depends": ['website'],
    "data": [
        "views/res_users_view.xml",
        "views/webclient_templates.xml",
    ],
    "demo": [],
    "qweb": [
        "static/src/xml/login_as.xml",
    ],
    "installable": True,
    "active": False,
}
