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
    "name": "Allotment Partner - Procurement",
    "version": "0.1",
    "depends": ["sale_stock"],
    "author": "Smile",
    "description": """This module aims to follow the assigned partner into a sale order line
    and get this information in the procurement order.
    You can try also this module if you need to manage your purchases : smile_allotment_partner_purchase

    In France, this tracking is particular and define like "contre-marque".

    This module built and test on OpenERP v7.0.

    Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr & bruno.joliveau@smile.fr
    """,
    "summary": "",
    "website": "http://www.smile.fr",
    "category": 'Hidden/Dependency',
    "sequence": 20,
    "init_xml": [
        "security/allotment_partner_procurement_security.xml",
    ],
    "update_xml": [
        "view/procurement_view.xml",
        "view/sale_view.xml",
    ],
    'demo_xml': [],
    'test': [],
    "auto_install": False,
    "installable": True,
    "application": False,
}
