# -*- coding: utf-8 -*-
# (C) 2013 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import inspect
import logging
import os
import time

from odoo import tools
from odoo.modules.registry import Registry
from odoo.osv import osv, orm
from odoo.tools import config

from .upgrade import UpgradeManager

_logger = logging.getLogger(__name__)

native_new = Registry.new


@classmethod
def new(cls, db_name, force_demo=False, status=None, update_module=False):
    callers = [frame[3] for frame in inspect.stack()]
    if 'preload_registries' not in callers and \
            '_initialize_db' not in callers:
        return native_new(db_name, force_demo, status, update_module)
    with cls._lock:
        upgrades = False
        try:
            with UpgradeManager(db_name) as upgrade_manager:
                upgrades = upgrade_manager.upgrades
                if upgrades:
                    t0 = time.time()
                    _logger.info('loading %s upgrade...',
                                 upgrade_manager.code_version)
                    max_cron_threads = config.get('max_cron_threads')
                    config['max_cron_threads'] = 0
                    init, update = \
                        dict(config['init']), dict(config['update'])
                    if not upgrade_manager.db_in_creation:
                        upgrade_manager.pre_load()
                        config['update'].update({
                            module: True for module in
                            upgrade_manager.modules_to_upgrade
                        })
                    else:
                        config['init'].update({
                            module: True for module in
                            upgrade_manager.modules_to_install_at_creation
                        })
                    native_new(db_name, force_demo, status, True)
                    config['init'], config['update'] = init, update
                    upgrade_manager.post_load()
                    upgrade_manager.reload_translations()
                    upgrade_manager.set_db_version()
                    config['max_cron_threads'] = max_cron_threads
                    _logger.info('%s upgrade successfully loaded in %ss',
                                 upgrade_manager.code_version,
                                 time.time() - t0)
                else:
                    _logger.info('no upgrade to load')
            # Remove base from 'init', to avoid update of the module
            config['init'].pop('base', None)
            registry = native_new(db_name, force_demo, status, update_module)
            if upgrades and config.get('stop_after_upgrades'):
                _logger.info('Stopping Odoo server')
                os._exit(0)
            return registry
        except Exception as e:
            if upgrades and config.get('stop_after_upgrades'):
                msg = isinstance(e, (osv.except_osv, orm.except_orm)) and \
                    e.value or e
                _logger.error(tools.ustr(msg), exc_info=True)
                _logger.critical('Upgrade FAILED')
                _logger.info('Stopping Odoo server')
                os._exit(1)
            raise


Registry.new = new
