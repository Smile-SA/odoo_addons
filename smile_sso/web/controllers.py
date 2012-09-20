# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Smile (<http://www.smile.fr>). All Rights Reserved
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

import simplejson
import urllib2

from werkzeug.utils import redirect

import openerp
from web.common import http as openerpweb
from web.controllers.main import WebClient, Session

config_options = openerp.tools.config.options or {}
sso_portal = config_options.get('smile_sso.portal_redirect') or '/'


def _get_connection_info(req, **kwargs):
    db = None
    for k in kwargs:
        if k == 'db':
            db = kwargs[k]
    return (db or req.session._db or config_options.get('db_name'),
            req.httprequest.headers.get('Remote-User'),
            config_options.get('smile_sso.shared_secret_pin'))


def _check_connection_info(db, user, security_key):
    if not db:
        openerpweb._logger.info("Missing database parameter")
    if not user:
        openerpweb._logger.info("No user provided")
    if not security_key:
        openerpweb._logger.info("Missing shared secret PIN")


@openerpweb.httprequest
def sso_login(self, req, **kwargs):
    db, login, security_key = _get_connection_info(req, **kwargs)
    _check_connection_info(db, login, security_key)
    if db and login and security_key:
        user_info = req.session.proxy('common').sso_login(db, login, security_key)
        if user_info and user_info['id'] > 0:
            req.session.bind(db, user_info['id'], login, user_info['password'])
            req.session.get_context()
        elif sso_portal == '/':
            req.session.authenticate(db, login, security_key, {})
        else:
            return redirect(sso_portal)
        addr = redirect('/web/webclient/home', 303)
        cookie_val = urllib2.quote(simplejson.dumps(req.session_id))
        addr.set_cookie('session0|session_id', cookie_val)
        return addr
    return redirect(sso_portal)


def destroy(self, req, **kwargs):
    db, user, security_key = _get_connection_info(req, **kwargs)
    _check_connection_info(db, user, security_key)
    if db and user and security_key:
        req.session.proxy('common').sso_logout(db, user, security_key)
    req.session._suicide = True


@openerpweb.httprequest
def sso_logout(self, req, **kwargs):
    destroy(self, req, **kwargs)
    return redirect(sso_portal)

Session.destroy = openerpweb.jsonrequest(destroy)
WebClient.sso_login = sso_login
WebClient.sso_logout = sso_logout
