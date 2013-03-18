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
    "name": "Cross Selling",
    "version": "0.1",
    "depends": ["sale"],
    "author": "Smile",
    "description": """This module aims to increase your business.

    The product get a new tab to link product between themselves.
    You can input properties on each product you link and manage the pricelist or a special price to bypass the pricelist.

    When you encode a new sale order and you select a main product with links,
    OpenERP shows you a pop-up to choose the product you can add in new lines.

    Thanks to Camptocamp. We had this idea from their module "product_link".
    We prefered make a new module because we didn't want to depend on stock.

    This module built and test on OpenERP v7.0.

    Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr & bruno.joliveau@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Sales Management',
    "sequence": 20,
    "init_xml": [
        "security/ir.model.access.csv",
    ],
    "update_xml": [
        "view/product_view.xml",
    ],
    'demo_xml': [],
    'test': [],
    "auto_install": False,
    "installable": True,
    "application": False,
}
