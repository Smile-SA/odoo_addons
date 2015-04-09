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
    "name": "Budget Commitment",
    "version": "0.1",
    "depends": ["account_budget"],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Features

    * Allow to follow-up commitment per budget line
    * Define commitment limit per budget position and per user

Todo

    * Add tolerance percentage or fixed amount for over budget commitment

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Accounting & Finance',
    "sequence": 20,
    "data": [
        "security/ir.model.access.csv",
        "views/account_budget_view.xml",
        "views/res_users_view.xml",
        "data/account_data.xml"
    ],
    "demo": [
        "demo/account_demo.yml",
        "demo/account_budget_demo.xml",
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
