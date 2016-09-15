# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>).
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
    "name": "Access rules for Import",
    "version": "0.1",
    "depends": ['web', 'base_import'],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Add access rules for import features
====================================

For each user, you can indicate if it can import data

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Hidden',
    "sequence": 20,
    "data": [
        'security/web_import_security.xml',
        'views/webclient_templates.xml',
    ],
    "auto_install": True,
    "installable": True,
    "application": False,
}
