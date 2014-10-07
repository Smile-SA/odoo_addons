# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
#                       author cyril.gaspard@smile.fr
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
    "name": "Smile Payment Terms Auto",
    "version": "1.0",
    "depends": ["smile_payment_terms"],
    "author": "Smile",
    "description": """
    What do this module:
    give possibility to pay automatically the invoice if in payment terms,
    the box 'pay_auto' is checked.
    """,
    "website": "http://www.smile.fr",
    "category": "Generic Modules/Sales",
    "sequence": 10,
    "demo": [
    ],
    "data": [
        "account_view.xml",
        "account_invoice_view.xml",
        "translate.sql",
    ],
    "js": [
    ],
    "qweb": [
    ],
    "css": [
    ],
    "demo": [
    ],
    "test": [
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
