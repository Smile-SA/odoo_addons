import inspect
import logging
import os
import time
from odoo.exceptions import UserError
from odoo.modules.registry import Registry
from odoo.tools import config

from collections.abc import Collection

from odoo import tools
from .upgrade import UpgradeManager

_logger = logging.getLogger(__name__)

native_new = Registry.new


@classmethod
def new(
        cls,
        db_name: str,
        *,
        update_module: bool = False,
        install_modules: Collection[str] = (),
        upgrade_modules: Collection[str] = (),
        reinit_modules: Collection[str] = (),
        new_db_demo: bool | None = None,
):
    if not _is_db_initialization():
        return native_new(
            db_name,
            install_modules=install_modules,
            upgrade_modules=upgrade_modules,
            update_module=update_module,
            reinit_modules=reinit_modules,
            new_db_demo=new_db_demo
        )
    with cls._lock:
        upgrades = False
        try:
            with UpgradeManager(db_name) as upgrade_manager:
                upgrades = upgrade_manager.upgrades
                #  Get upgrade twice to refresh value if the first call was
                #  made before advisory_lock.
                #  This can lead to n upgrade in multi front configuration.
                if upgrades and upgrade_manager._get_upgrades():

                    t0 = time.time()
                    _logger.info("loading %s upgrade...",
                                 upgrade_manager.code_version)
                    initial_config = _get_initial_config()
                    _run_upgrade_pre(upgrade_manager)
                    native_new(
                        db_name,
                        install_modules=install_modules,
                        upgrade_modules=upgrade_modules,
                        update_module=update_module,
                        reinit_modules=reinit_modules,
                        new_db_demo=new_db_demo
                    )
                    _run_upgrade_post(upgrade_manager, initial_config)
                    _logger.info("%s upgrade successfully loaded in %ss",
                                 upgrade_manager.code_version,
                                 time.time() - t0)
                else:
                    _logger.info("no upgrade to load")
            # Remove base from "init", to avoid update of the module
            config["init"].pop("base", None)
            registry = native_new(
                db_name,
                install_modules=install_modules,
                upgrade_modules=upgrade_modules,
                update_module=update_module,
                reinit_modules=reinit_modules,
                new_db_demo=new_db_demo
            )
            if upgrades and config.get("stop_after_upgrades"):
                _logger.info("Stopping Odoo server")
                os._exit(0)
            return registry
        except Exception as e:
            _manage_upgrade_errors(upgrades, e)
            raise


def _is_db_initialization():
    callers = [frame[3] for frame in inspect.stack()]
    return "preload_registries" in callers or "_initialize_db" in callers


def _manage_upgrade_errors(upgrades, e):
    if upgrades and config.get("stop_after_upgrades"):
        msg = isinstance(e, UserError) and e.value or e
        _logger.error(tools.ustr(msg), exc_info=True)
        _logger.critical("Upgrade FAILED")
        _logger.info("Stopping Odoo server")
        os._exit(1)


def _get_initial_config():
    return config.get("max_cron_threads"), dict(config["init"]), \
        dict(config["update"])


def _run_upgrade_pre(upgrade_manager):
    config["max_cron_threads"] = 0
    if not upgrade_manager.db_in_creation:
        upgrade_manager.pre_load()

        modules_to_update = dict.fromkeys(
            upgrade_manager.modules_to_upgrade, True)
        config["update"].update(modules_to_update)
    else:
        config["init"].update(
            dict.fromkeys(
                upgrade_manager.modules_to_install_at_creation, True)
        )


def _run_upgrade_post(
        upgrade_manager, initial_config):
    max_cron_threads, init, update = initial_config
    config["init"], config["update"] = init, update
    upgrade_manager.post_load()
    upgrade_manager.reload_translations()
    upgrade_manager.set_db_version()
    config["max_cron_threads"] = max_cron_threads


Registry.new = new
