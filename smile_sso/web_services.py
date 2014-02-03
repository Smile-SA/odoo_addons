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

import logging

import security
from service.web_services import common

native_dispatch = common.dispatch


_logger = logging.getLogger("web-service")


def new_dispatch(self, method, params):
    if method in ('sso_login', 'sso_logout'):
        res = getattr(security, method)(params[0], params[1], params[2])
        msg = res and 'Successful %s' % method.replace('sso_', '') or 'Bad login or password'
        #TODO: log the client IP address..
        _logger.info("%s from '%s' using database '%s'" % (msg, params[1], params[0]))
        return res
    else:
        return native_dispatch(self, method, params)

common.dispatch = new_dispatch
