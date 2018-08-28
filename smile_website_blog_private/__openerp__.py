# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-Today OpenSur.
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
    'name': 'Smile Blogs private',
    'category': 'Website',
    'website': 'https://www.smile.fr',
    'summary': 'Blogs and post private access',
    'version': '1.00',
    'description': """
OpenERP Blog Private
====================
Add feature to have private blogs and post, visible only for certain security groups
Origine from https://github.com/OpenSur/Odoo_addons#8.0 convert to > 10
        """,
    'author': 'Smile SA',
    'depends': ['website_blog'],
    'data': [
        'data/access_rules.xml',
        'views/website_blog_private_views.xml'
    ],
    'demo': [
    ],
    'test': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
}
