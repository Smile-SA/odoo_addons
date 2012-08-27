# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 credativ Ltd (<http://credativ.co.uk>).
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
    "name": "Date, datetime & float ranges in search views.",
    "description": """
        1 - Replaces single date, datetime and float search fields to a range.
            This was the default behaviour in OpenERP 6.0 but was ditched in 6.1:
            => https://bugs.launchpad.net/openerp-web/+bug/926390

        2 - Allow selection of time in datetime search fields.
            Again, this was removed in 6.1:
            => https://bugs.launchpad.net/openerp-web/+bug/1037658
        """,
    "version": "1.1",
    "author": "Smile & credativ Ltd",
    "website": "http://smile.fr",
    "category": "Tools",
    "depends": ["web"],
    "js": [
        "static/src/js/search.js",
    ],
    "auto_install": False,
}
