# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>). All Rights Reserved
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
    'name': 'Smile Journal Item Usability',
    'version': '1.0',
    'depends': [
        'account',
    ],
    'author': 'Smile',
    'description': """
This module customize Journal Item:
1. Add new menu item for Journal Entries useful for accountants
2. Add new menu to track supplier due dated payments
    """,
    'summary': '',
    'website': 'http://www.smile.fr',
    'category': 'Accounting & Finance',
    'sequence': 10,
    'data': [
        'views/account_move_line_view.xml',
    ],
    'demo_xml': [],
    'test': [],
    'auto_install': False,
    'installable': True,
    'application': False,
}
