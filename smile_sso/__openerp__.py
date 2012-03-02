# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 OpenERP s.a. (<http://openerp.com>).
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
    'name': 'Smile SSO',
    'version': '0.1',
    'category': 'Tools',
    'description': """
This module delegate users authentification (global login and logout) to
Apache HTTP Server via some modules like mod_auth_cas, mod_auth_kerb or mod_auth_openid.

It just provides:
    * 2 new URLs: /openerp/sso_login and /openerp/sso_logout
    * 2 new methods in the "common" web service: sso_login and sso_logout

For this moment, the web service "sso_login" is protected by a simple password shared between web client and openerp server.
We plan to strengthen this call by validating the SSL certificate of web client into openerp server.

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
""",
    'author': 'Smile',
    'website': 'http://www.smile.fr',
    'depends': ['base'],
    'init_xml' : [],
    'update_xml': [],
    'installable': True,
    'active': False,
    'web': True,
}
