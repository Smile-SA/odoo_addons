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

from openerp.service import model
from openerp.addons.web.controllers.main import Home

from openerp.addons.smile_upgrade.web.controllers import maintenance

_logger = logging.getLogger(__package__)


def kill_xmlrpc_services(*args):
    _logger.error("Service in maintenance. Call args: %s", args)
    raise IOError('Connection refused. Service in maintenance')


class MaintenanceManager(object):
    """Maintenance Manager
    * Replace classic home by maintenance page
    * Reject xmlrpc connections
    """

    def __init__(self):
        self.classic_home = Home.index
        self.model_dispatch = model.dispatch

    def start(self):
        Home.index = maintenance
        model.dispatch = kill_xmlrpc_services

    def stop(self):
        Home.index = self.classic_home
        model.dispatch = self.model_dispatch

