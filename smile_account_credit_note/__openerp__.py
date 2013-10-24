# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name": "Credit Notes Management",
    "version": "0.2",
    "depends": ["account_voucher"],
    "author": "Smile",
    "description": """Credit Notes Management

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "website": "http://www.smile.fr",
    "category": "Accounting & Finance",
    "sequence": 32,
    "init_xml": [],
    "update_xml": [
        'view/account_voucher_view.xml',
        'view/account_view.xml',
    ],
    "demo_xml": [],
    'test': [],
    "auto_install": False,
    "installable": True,
    "application": False,
}
