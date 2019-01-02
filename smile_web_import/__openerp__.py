# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Smile (<http://www.smile.fr>).
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
    "author": "Smile",
    "category": 'Tools',
    "description": """
Add access rules for import features
====================================

For each user, you can indicate if it can import data

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "depends": ['web', 'smile_has_group'],
    "website": "http://www.smile.fr",
    "license": 'AGPL-3',
    "sequence": 20,
    'init_xml': [
    ],
    'update_xml': [
        'security/web_import_security.xml',
    ],
    'js' : [
        'static/src/js/web_import.js',
    ],
    'auto_install': False,
}
