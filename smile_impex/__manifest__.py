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
    "name": "Import / Export",
    "version": "1.0",
    "depends": ['smile_log'],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Import / Export

Features

    # Define an import/export template by
        * choose a model
        * define a method to import/export records
        * define a domain to filter lines to export
    # Create actions to generate a new import/export
        * a client action to generate an export on the fly from records list
        * a scheduled action to generate periodically a new import/export
    # Log execution exceptions

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
& isabelle.richard@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "data": [
        'security/ir.model.access.csv',
        'views/export_view.xml',
        'views/import_view.xml',
        'views/menu_view.xml',
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
