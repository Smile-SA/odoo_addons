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
import os
import sys
import time

from openerp import tools
from openerp.modules.registry import RegistryManager
from openerp.osv import osv, orm
from openerp.tools import config

from .upgrade import UpgradeManager

_logger = logging.getLogger(__name__)

native_new = RegistryManager.new


@classmethod
def new(cls, db_name, force_demo=False, status=None, update_module=False):
    with cls.lock():
        upgrades = False
        try:
            with UpgradeManager(db_name) as upgrade_manager:
                upgrades = upgrade_manager.upgrades
                if upgrades:
                    cls.signal_registry_change(db_name)
                    t0 = time.time()
                    _logger.info('loading %s upgrade...', upgrade_manager.code_version)
                    if not upgrade_manager.db_in_creation:
                        upgrade_manager.pre_load()
                        modules = upgrade_manager.modules_to_upgrade
                    else:
                        modules = upgrade_manager.modules_to_install_at_creation
                    if modules:
                        registry = native_new(db_name, force_demo)
                        upgrade_manager.force_modules_upgrade(registry, modules)
                    native_new(db_name, force_demo, update_module=True)
                    upgrade_manager.post_load()
                    upgrade_manager.set_db_version()
                    _logger.info('%s upgrade successfully loaded in %ss',
                                 upgrade_manager.code_version, time.time() - t0)
            registry = native_new(db_name, force_demo, update_module=update_module)
            if upgrades and config.get('stop_after_upgrades'):
                _logger.info('Stopping Odoo server')
                os._exit(0)
            return registry
        except Exception, e:
            e.traceback = sys.exc_info()
            if upgrades and config.get('stop_after_upgrades'):
                msg = isinstance(e, (osv.except_osv, orm.except_orm)) and e.value or e
                _logger.error(tools.ustr(msg), exc_info=e.traceback)
                _logger.critical('Upgrade FAILED')
                _logger.info('Stopping Odoo server')
                os._exit(1)
            raise

RegistryManager.new = new
