# -*- coding: utf-8 -*-

import inspect
import logging
import os

from odoo import models


_logger = logging.getLogger(__name__)


class IrModuleModule(models.Model):
    _inherit = 'ir.module.module'

    def __is_recursively_called(self):
        """
        Return True if the method was called more than once,
        ie. if the method is calling herself.
        """
        current_file = os.path.abspath(__file__)
        recursion_count = [
            file_path == current_file and function_name == '_register_hook'
            for file_path, function_name in [
                (frame[1], frame[3]) for frame in inspect.stack()
            ]
        ].count(True)
        return recursion_count > 1

    def __db_in_creation(self):
        return not bool(self._get_saved_checksums())

    def _register_hook(self):
        """
        This method is called after Odoo finished setting up the registry.
        We check if any module was updated, ie. its checksum changes.
        Automatically upgrade changed modules, except in db creation mode.
        To avoid recursion loop, we check if the method was already
        called by adding some modules in update list.
        """
        super()._register_hook()
        if self.__db_in_creation() or self.__is_recursively_called():
            return
        _logger.info("Upgrade changed modules...")
        self.upgrade_changed_checksum(overwrite_existing_translations=True)
        _logger.info("Changed modules upgraded.")
