# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name": "Sales Management - Product Options",
    "version": "0.1",
    "license": 'AGPL-3',
    "depends": [
        "smile_product_option",
        "sale",
    ],
    "author": "Smile",
    "description": """
Product Options (Sales Management)
==================================

Manage product options in quotations/sale orders.
Allow to specify if an option is hidden in sale order and/or if its price is included in the price of main product.

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": "Sales",
    "sequence": 20,
    "data": [
        "views/product_view.xml",
        "views/sale_view.xml",
        "views/report_saleorder.xml",
    ],
    'demo': [
        "demo/product.option.csv",
    ],
    'test': [],
    "auto_install": False,
    "installable": True,
    "application": False,
}
