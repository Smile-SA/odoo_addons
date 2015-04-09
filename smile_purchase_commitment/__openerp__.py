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
    "name": "Purchase Commitment",
    "version": "0.1",
    "depends": ["purchase", "smile_account_budget_commitment"],
    "author": "Smile",
    "license": 'AGPL-3',
    "description": """
Features

    * Generate analytic lines at purchase confirmation / cancellation
    * Allow to follow-up purchase commitment per budget line
    * Define purchase commitment limit per budget position and per user
    * Allow to select a purchase validator who has commitment authorizations

TODO

    * Manage gap between purchase order(s) and supplier invoice(s)

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Purchase Management',
    "sequence": 20,
    "data": [
        'views/purchase_view.xml',
    ],
    "auto_install": False,
    "installable": True,
    "application": False,
}
