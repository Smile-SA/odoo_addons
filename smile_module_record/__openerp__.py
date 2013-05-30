# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name": "Export Customizations as a Module",
    "version": "0.1",
    "depends": ["base"],
    "author": "Smile",
    "description": """
    This module aims to export data in a new module containing CSV files.

    This module built and test on OpenERP v7.0.

    Features
        * Export data in CSV through a new module compatible with import (i.e. data files are ordered and splitted if necessary)
        * Export automatically properties linked to selected models

    TODO
        * Manage workflow - Eg.: export a validated invoice and import it at this same state, in particular if account moves were exported

    Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr & bruno.joliveau@smile.fr
    """,
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "init_xml": [],
    "update_xml": [
        "wizard/base_module_record_view.xml",
    ],
    'demo_xml': [],
    'test': [],
    "auto_install": True,
    "installable": True,
    "application": False,
}
