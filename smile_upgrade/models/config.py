# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import os
import sys

from odoo.tools import config
from odoo.tools.safe_eval import safe_eval

if sys.version_info > (3,):
    from configparser import ConfigParser, NoSectionError
else:
    from ConfigParser import ConfigParser, NoSectionError

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
            _logger.warning("Unspecified 'upgrades_path' option "
                            "in Odoo configuration file")
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
        config = ConfigParser()
        try:
            config.readfp(open(config_file))
            for (key, value) in config.items('options'):
                if value in ('True', 'False'):
                    value = safe_eval(value)
                self.options[key] = value
            for section in config.sections():
                if section != 'options':
                    _logger.warning("Only options section is taken into "
                                    "account in upgrades configuration")
        except (IOError, NoSectionError):
            return


configuration = ConfigManager()
