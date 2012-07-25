# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
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

import cherrypy

import openobject.tools
from openobject.tools import expose, redirect
from openerp.controllers import SecuredController, unsecured
from openerp.controllers.root import Root
from openerp.controllers.utils import login
from openerp.utils import rpc

sso_portal = cherrypy.config.get('smile_sso.portal_redirect') or '/'


def _get_connection_info(db):
    return (db or cherrypy.config.get('openerp.server.database'),
            cherrypy.request.headers.get('REMOTE-USER'),
            cherrypy.config.get('smile_sso.shared_secret_pin'))


def _check_connection_info(db, user, security_key):
    if not db:
        cherrypy.log("Missing database parameter", 'SMILE_SSO')
    if not user:
        cherrypy.log("No user provided", 'SMILE_SSO')
    if not security_key:
        cherrypy.log("Missing shared secret PIN", 'SMILE_SSO')


@expose()
@unsecured
def sso_login(self, db=None, *args, **kwargs):
    db, user, security_key = _get_connection_info(db)
    _check_connection_info(db, user, security_key)
    if db and user and security_key:
        user_info = rpc.session.execute_noauth('common', 'sso_login', db, user, security_key)
        if user_info and user_info['id'] > 0:
            rpc.session._logged_as(db, user_info['id'], user_info['password'])
            raise redirect('/')
        elif sso_portal == '/':
            return login(sso_portal, message=_('Unknown user!'), db=db, user=user, action='sso_login')
    raise redirect(sso_portal)


@expose()
@unsecured
def sso_logout(self, db=None, *args, **kwargs):
    db, user, security_key = _get_connection_info(db)
    _check_connection_info(db, user, security_key)
    if db and user and security_key:
        rpc.session.execute_noauth('common', 'sso_logout', db, user, security_key)
    rpc.session.logout()  # Same behaviour as the original Root.logout() method
    raise redirect(sso_portal)

Root.sso_login = sso_login
Root.sso_logout = sso_logout

# Map requests to standard login/login URLs to their SSO counterparts
url_method_orig = openobject.tools.url


def url_method_wrapper(self_class, *args, **kwargs):
    normalized_url = url_method_orig(self_class, *args, **kwargs)
    # We can't enforce standard login screen redirection unless we solve ticket
    # 2 (see: https: //github.com/Smile-SA/smile_openerp_addons_6.0/issues/2 )
    # if normalized_url.startswith('/login'):
    #    normalized_url = '/sso_login'
    if normalized_url.startswith('/logout'):
        normalized_url = '/sso_logout'
    return normalized_url
# Do not enforce login/logout via SSO methods if no third-party SSO portal is defined: keep standard OpenERP login/logout screen and redirec behaviour
if sso_portal != '/':
    Root.logout = sso_logout
    openobject.tools.url = url_method_wrapper
