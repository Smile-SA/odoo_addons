# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name": "Budget Commitment Forecast",
    "version": "0.1",
    "depends": [
        "smile_commitment_base",
    ],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Features

    * Allow to follow commitment forecast per budget line

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Accounting & Finance',
    "sequence": 20,
    "data": [
        "views/account_analytic_view.xml",
        "views/account_budget_view.xml",
    ],
    "demo": [],
    "auto_install": False,
    "installable": True,
    "application": False,
}
