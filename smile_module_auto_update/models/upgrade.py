# -*- coding: utf-8 -*-

import logging

from odoo import api, SUPERUSER_ID

from odoo.addons.smile_upgrade.models.upgrade import UpgradeManager

_logger = logging.getLogger(__name__)

native_post_load = UpgradeManager.post_load


def post_load(self):
    """
    Save checksums of all installed modules in db creation mode.
    Do nothing if module module_auto_update is not installed,
    ie. if method _save_installed_checksums is not available on
    model ir.module.module.
    """
    native_post_load(self)
    if self.db_in_creation:
        with self.db.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            IrModuleModule = env['ir.module.module']
            if '_save_installed_checksums' in dir(IrModuleModule):
                _logger.info("Save checksums of all installed modules...")
                IrModuleModule._save_installed_checksums()
                _logger.info("Checksums of all installed modules saved.")


UpgradeManager.post_load = post_load
