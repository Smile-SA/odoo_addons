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

from openerp.modules.registry import Registry, RegistryManager
from openerp.tools import config

from maintenance import MaintenanceManager
from upgrade import UpgradeManager

_logger = logging.getLogger('upgrades')


def set_db_version(self, version):
    if version:
        cr = self.db.cursor()
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
def new(cls, db_name, force_demo=False, status=None, update_module=False, pooljobs=True):
    code_at_creation = False
    with cls.upgrade_manager(db_name) as upgrade_manager:
        if upgrade_manager.db_in_creation:
            code_at_creation = upgrade_manager.code_version
        for upgrade in upgrade_manager.upgrades:
            upgrade.pre_load()
            if upgrade.modules_to_upgrade:
                registry = native_new(db_name, pooljobs=False)
                upgrade.force_modules_upgrade(registry)
            native_new(db_name, update_module=True, pooljobs=False)
            upgrade.post_load()
    registry = native_new(db_name, force_demo, status, update_module, pooljobs)
    registry.set_db_version(code_at_creation)
    if config.get('stop_after_upgrades'):
        _logger.info('Stopping OpenERP server')
        os._exit(0)
    return registry

RegistryManager.upgrade_manager = upgrade_manager
RegistryManager.new = new
