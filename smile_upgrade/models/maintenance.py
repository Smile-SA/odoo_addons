# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp import http

_logger = logging.getLogger(__package__)


def rpc_down(origin):
    def wrapper(service_name, method, params):
        _logger.error("Service in maintenance. Call args: %s", ((service_name, method, params),))
        raise IOError('Connection refused. Service in maintenance')
    wrapper._origin = origin
    return wrapper


class MaintenanceManager(object):
    """Maintenance Manager
    * Replace classic home by maintenance page
    * Reject RPC connections
    """

    def start(self):
        http.dispatch_rpc = rpc_down(http.dispatch_rpc)
        from ..controllers.main import Maintenance
        self.module = Maintenance

    def stop(self):
        http.dispatch_rpc = http.dispatch_rpc._origin
        if 'index' in self.module.__dict__:
            del self.module.index
