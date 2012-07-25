# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 OpenERP s.a. (<http: //openerp.com>).
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
    'name': 'Smile Cache Exceptions',
    'version': '0.1',
    'category': 'Tools',
    'description': """Smile Cache Exceptions

Don't cache fields_view_get and fields_get methods for models indicated via cache.exceptions in web client config file

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
""",
    'author': 'Smile',
    'website': 'http: //www.smile.fr',
    'depends': ['base'],
    'init_xml': [],
    'update_xml': [],
    'installable': True,
    'active': False,
    'web': True,
}
