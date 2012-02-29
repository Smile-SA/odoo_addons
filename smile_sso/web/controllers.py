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

from openobject.tools import expose, redirect
from openerp.controllers import SecuredController, unsecured
from openerp.controllers.root import Root
from openerp.controllers.utils import login
from openerp.utils import rpc

def _get_connection_info(db):
    return [
        db or cherrypy.config.get('openerp.server.database'),
        cherrypy.request.headers.get('REMOTE_USER') or 'demo', #or 'demo' is just here for tests
        cherrypy.config.get('server.authentification_key'),
    ]

@expose()
@unsecured
def sso_login(self, db=None):
    db, user, security_key = _get_connection_info(db)
    if db and user and security_key:
        user_info = rpc.session.execute_noauth('common', 'sso_login', db, user, security_key)
        if user_info and user_info['id'] > 0:
            rpc.session._logged_as(db, user_info['id'], user_info['password'])
        else:
            return login('/', message=_('Unknown user!'), db=db, user=user, action='sso_login')
    raise redirect('/')

@expose()
@unsecured
def sso_logout(self, db=None):
    db, user, security_key = _get_connection_info(db)
    if db and user and security_key:
        if rpc.session.execute_noauth('common', 'sso_logout', db, user, security_key):
            rpc.session.logout()
    raise redirect('/')

Root.sso_login = sso_login
Root.sso_logout = sso_logout
