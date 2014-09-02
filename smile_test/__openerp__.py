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
    "name": "Smile Tests",
    "version": "0.1",
    "depends": ["base"],
    "author": "Smile",
    "description": """
Generic tests

Features = Test for all models:

    * search count / search with limit=1 / global search
    * read first item / read all
    * name_get
    * default view
    * domain and context in action window
    * domain in record rule

TODO

    * Check all views

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr & isabelle.richard@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Hidden',
    "sequence": 20,
    "test": [
        "test/general_read_test.yml",
        "test/act_window_test.yml",
        "test/fields_view_get_test.yml",
        "test/ir_rule.yml",
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
