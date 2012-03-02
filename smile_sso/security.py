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

import pooler
from tools import config

def _check_security_key(security_key):
    # TODO: improve it and provides a ssl certification check
    return int(security_key) == int(config.get('web_server_authentification_key'))

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
