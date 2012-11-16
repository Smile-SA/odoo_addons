# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Smile (<http://www.smile.fr>).
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
    "name": "Hide all create and duplicate buttons of some models.",
    "description": """
        This module is designed for OpenERP 6.1 web client. This module is not
        supposed to be a generic module. It's a demonstration on how-to create
        a custom module to apply dirty patches to the web client UI.

        It currently hide all create and duplicate buttons of a given object model,
        by monkey-patching the Javascript code of views and fields. The list of
        models it affects is hard-coded in the ./static/src/js/custom.js file.
        """,
    "version": "1.0",
    "author": "Smile",
    "website": "http://smile.fr",
    "category": "Tools",
    "depends": ["web"],
    "js": [
        "static/src/js/custom.js",
    ],
    "auto_install": False,
}
