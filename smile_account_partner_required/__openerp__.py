# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name": "Account Partner Required",
    "version": "0.1",
    "depends": ["account"],
    "author": "Smile",
    'description': """
         This module adds an option "partner policy" on account.\n

         You have the choice between 3 policies :\n
            # Optional (the default)\n
            # Always (require a partner)\n
            # Never (forbid a partner)\n

         This module is useful to enforce a partner on account move lines on customer and supplier accounts.\n

        Suggestions & Feedback to: mohamed.boujdid@smile-maroc.com
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Accounting & Finance',
    "sequence": 20,
    "data": [
        'views/account_view.xml'
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
