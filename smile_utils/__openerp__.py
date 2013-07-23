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
    "name": "Smile Utils",
    "version": "0.1",
    "depends": ["mail"],
    "author": "Smile",
    "description": """Smile Utils

    * decode_csv_reader: a function to decode csv content to unicode
    * get_exception_message: a function to get exception message from OpenERP or native Python exception
    * clean_string: a function to strip accents and replace non ascii characters by space
    * timeme: a decorator to get the execution time of a function

    Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Tools',
    "sequence": 20,
    "init_xml": [],
    "update_xml": [],
    'demo_xml': [],
    'test': [],
    "auto_install": False,
    "installable": True,
    "application": False,
}
