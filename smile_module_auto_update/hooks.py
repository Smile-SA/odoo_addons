# -*- coding: utf-8 -*-

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def post_init(cr, registry):
    save_installed_checksums(cr, registry)


def save_installed_checksums(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    IrModuleModule = env['ir.module.module']
    # TODO: save checksum only if module is installed *after*
    # database initialization via smile_upgrade
    _logger.info("Save checksums of all installed modules...")
    IrModuleModule._save_installed_checksums()
    _logger.info("Checksums of all installed modules saved.")
