# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
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
    "name" : "Invoicing Plan for Sales",
    "version" : "1.0",
    "category" : "Generic Modules/Sales & Purchases",
    "author" : "Smile",
    "website": 'http://www.smile.fr',
    "description": """  
                Manage go between commissions.
                    Manage business providers
                    Specify in sale order the business provider partner
                    Specify price list to apply
                    Specify sale order lines affected with commission
                    Generate  purchase order of business provider partner from invoiced sale order line affected with commissions.
                    
    Suggestions & Feedback to: samir.rachedi@smile.fr & corentin.pouhet-brunerie@smile.fr
    """,
    "depends" : ['sale','purchase','smile_product_combine_pricelist'],
    "init_xml" : [],
    "update_xml": [
        'sale_view.xml',
        'partner_view.xml',
        'wizard/compute_commission_view.xml'
    ],
    "test": [
             ],
    "demo_xml" : [],
    "installable": True,
    "active": False,
    "certificate": '',
}
