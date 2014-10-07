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
    "name": "Smile Gift Wrap",
    "version": "1.0",
    "depends": ["stock",
                "sale_stock"
                ],
    "author": "Smile",
    "description":
    """This module manage the use of gifts in sale orders and pickings""",

    "data": [
        "view/product_view.xml",
        "data/product_data.xml",
        "view/sale_order_line_view.xml",
        "view/stock_move_view.xml",
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
