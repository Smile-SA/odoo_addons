# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>). All Rights Reserved
#                       author cyril.defaria@smile.fr
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
    "name": "Smile Sale Delivery Date",
    "version": "1.0",
    "depends": ["sale", "sale_stock"],
    "author": "Smile",
    "description": """
    What do this module:
    Replace the field "delay" of the sale.order.line by a field named "delivery_date" based on the today date"
    The move stock generated must have the right date_expected (based on the new "delivery_date", and not anymore on the "delay")
    """,
    "website": "http://www.smile.fr",
    "category": "Generic Modules/Sales",
    "sequence": 10,
    "data": [
        "view/sale_view.xml",
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
