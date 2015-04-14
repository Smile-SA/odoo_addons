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

from contextlib import contextmanager
import logging
import os
import sys

from openerp import tools
from openerp.modules.registry import Registry, RegistryManager
from openerp.osv import osv, orm
from openerp.tools import config

from maintenance import MaintenanceManager
from upgrade import UpgradeManager

_logger = logging.getLogger(__package__)


def _get_exception_message(exception):
    msg = isinstance(exception, (osv.except_osv, orm.except_orm)) and exception.value or exception
    return tools.ustr(msg)


def set_db_version(self, version):
    if version:
        cr = self._db.cursor()
        try:
            cr.execute("INSERT INTO ir_config_parameter (key, value) VALUES ('code.version', %s)", (version,))
            cr.commit()
        finally:
            cr.close()

Registry.set_db_version = set_db_version

native_new = RegistryManager.new


@classmethod
@contextmanager
def upgrade_manager(cls, db_name):
    upgrade_manager = UpgradeManager(db_name)
    maintenance = MaintenanceManager()
    try:
        maintenance.start()
        yield upgrade_manager
    finally:
        upgrade_manager.cr.commit()
        upgrade_manager.cr.close()
        maintenance.stop()


@classmethod
def new(cls, db_name, force_demo=False, status=None, update_module=False):
    with cls.lock():
        upgrades = False
        try:
            code_at_creation = False
            with cls.upgrade_manager(db_name) as upgrade_manager:
                if upgrade_manager.db_in_creation:
                    code_at_creation = upgrade_manager.code_version
                upgrades = bool(upgrade_manager.upgrades)
                for upgrade in upgrade_manager.upgrades:
                    _logger.info('loading %s upgrade...', upgrade.version)
                    upgrade.pre_load()
                    if upgrade.modules_to_upgrade:
                        registry = native_new(db_name)
                        upgrade.force_modules_upgrade(registry)
                    native_new(db_name, update_module=True)
                    upgrade.post_load()
                    _logger.info('%s upgrade successfully loaded', upgrade.version)
            registry = native_new(db_name, force_demo, status, update_module)
            registry.set_db_version(code_at_creation)
            if upgrades and config.get('stop_after_upgrades'):
                _logger.info('Stopping Odoo server')
                os._exit(0)
            return registry
        except Exception, e:
            e.traceback = sys.exc_info()
            if upgrades and config.get('stop_after_upgrades'):
                _logger.error(_get_exception_message(e), exc_info=e.traceback)
                _logger.critical('Upgrade FAILED')
                _logger.info('Stopping Odoo server')
                os._exit(1)
            raise

RegistryManager.upgrade_manager = upgrade_manager
RegistryManager.new = new
