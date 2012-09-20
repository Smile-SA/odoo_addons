# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Smile (<http://www.smile.fr>).
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
    'version': '2.0',
    'category': 'Hidden',
    'description': """
This module delegate users authentification (global login and logout) to
Apache HTTP Server via some modules like mod_auth_cas, mod_auth_kerb or mod_auth_openid.

It just provides:
    * 2 new URLs: /web/webclient/sso_login and /web/webclient/sso_logout
    * 2 new methods in the "common" web service: sso_login and sso_logout

For this moment, the web service "sso_login" is protected by a simple password shared between web client and OpenERP server.
We plan to strengthen this call by validating the SSL certificate of web client into OpenERP server.

Configuration steps: Add in your config file
        * database name: db_name
        * secret pin number: smile_sso.shared_secret_pin
        * web addons: server_wide_modules = web,smile_sso

Suggestions & Feedback to: corentin.pouhet-brunerie@smile.fr
""",
    'author': 'Smile',
    'website': 'http://www.smile.fr',
    'depends': ['web'],
    'init_xml': [
        'security/ir.model.access.csv',
        'data/res_users_data.xml',
    ],
    'update_xml': [
        'view/res_users_view.xml',
    ],
    'auto_install': True,
}
