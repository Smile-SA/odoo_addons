# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Smile (<http://www.smile.fr>).
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Smile Workdays',
    'version': '0.1',
    'category': 'Tools',
    'description': """Defines objects that differenciates workdays from non-workdays

    Development in progress
    """,
    'author': 'Smile.fr',
    'website': 'http://www.smile.fr',
    'depends': ['base'],
    'init_xml': [
    ],
    'update_xml': [
        'security/ir.model.access.csv',
        'view/workdays.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
}
