# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010-2011 Smile (<http: //smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http: //www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Combine multiple pricelists',
    'version': '1.0',
    'category': 'Generic Modules/Sales & Purchases',
    'description': """
                        Combine multiple pricelists. Applying the first one and choose to deduct a price then reapply the follows.
                        Combine products to set a price:
                            The price of a product is based on the amount taken for other products.
                            This module must be inherited from other specific modules to be used
    """,
    'author': 'Smile.fr',
    'website': 'http: //www.smile.fr',
    'depends': [
        'product',
    ],
    'init_xml': [],
    'update_xml': [],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
}
