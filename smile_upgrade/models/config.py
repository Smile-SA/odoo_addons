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

import ConfigParser
import logging
import os

from openerp.tools import config
from openerp.tools.safe_eval import safe_eval as eval

_logger = logging.getLogger(__package__)


class ConfigManager(object):
    """Configuration Manager"""

    def __init__(self):
        self.options = {}
        self._get_default_options()
        self.load()

    def get(self, key, default=None):
        return self.options.get(key, default)

    def _get_default_options(self):
        upgrade_path = config.get('upgrades_path', '')
        if not upgrade_path:
            _logger.warning("Unspecified 'upgrades_path' option in Odoo configuration file")
            return
        if not os.path.exists(upgrade_path) or not os.path.isdir(upgrade_path):
            _logger.error("Specified 'upgrades_path' option is not valid")
            return
        self.options['upgrades_path'] = upgrade_path
        config_file = os.path.join(upgrade_path, 'upgrade.conf')
        if not os.path.exists(config_file) or not os.path.isfile(config_file):
            _logger.error(u"'upgrade.conf' doesn't exist in %s", upgrade_path)
            return
        self.options['config_file'] = config_file

    def load(self):
        config_file = self.options.get('config_file')
        if not config_file:
            return
        config = ConfigParser.ConfigParser()
        try:
            config.readfp(open(config_file))
            for (key, value) in config.items('options'):
                if value in ('True', 'False'):
                    value = eval(value)
                self.options[key] = value
            for section in config.sections():
                if section != 'options':
                    _logger.warning("Only options section is taken into account in upgrades configuration")
        except (IOError, ConfigParser.NoSectionError):
            return

configuration = ConfigManager()
