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

import netsvc
import pooler
from tools import config
from osv import osv


def _check_security_key(security_key):
    # Database parameter is absolutely required to prevent cold start errors.
    # For details, see ticket #2: https://github.com/Smile-SA/smile_openerp_addons_6.0/issues/2
    if not config.get('db_name'):
        raise osv.except_osv('smile_sso error !', "'db_name' is required in server configuration file")
    # Validate shared secret
    # TODO: improve it and provides a ssl certification check
    secret_match = int(security_key) == int(config.get('smile_sso.shared_secret_pin'))
    if not secret_match:
        logger = netsvc.Logger()
        logger.notifyChannel('smile_sso', netsvc.LOG_ERROR, "Server and web client don't share the same secret PIN number")
    return secret_match


def sso_login(db, login, security_key):
    if _check_security_key(security_key):
        pool = pooler.get_pool(db)
        return pool.get('res.users').sso_login(db, login)
    return False


def sso_logout(db, login, security_key):
    if _check_security_key(security_key):
        pool = pooler.get_pool(db)
        return pool.get('res.users').sso_logout(db, login)
    return False
