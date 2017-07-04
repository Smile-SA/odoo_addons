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
    "name": "Modules Graph",
    "version": "0.1",
    "depends": ["base"],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
    Generate Modules Graph from Odoo's user interface with upward, downward tree view or both.
    You need to install Graphviz to print graph. More infos on http://www.graphviz.org
    You can install it with pip: pip install pydot

    Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "website": "http://www.smile.fr",
    "category": "Hidden",
    "sequence": 32,
    "data": [
        "wizard/ir_module_graph_wizard_view.xml",
        "views/module_view.xml",
    ],
    "demo": [],
    'test': [],
    "auto_install": False,
    "installable": True,
    "application": False,
    'external_dependencies': {
        'python': ['pydot'],
    }
}
