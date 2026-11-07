import logging
import os

from odoo.tools import config, str2bool
from odoo.tools.safe_eval import safe_eval

from configparser import ConfigParser, NoSectionError, RawConfigParser

_logger = logging.getLogger(__package__)

# Section of the Odoo configuration file holding the smile_upgrade options
SECTION = "smile_upgrade"


def _read_section_options():
    parser = RawConfigParser()
    if config["config"]:
        parser.read(config["config"])
    return dict(parser.items(SECTION)) if parser.has_section(SECTION) else {}


_section_options = _read_section_options()


def get_odoo_option(key, default=None):
    """Return a smile_upgrade option of the Odoo configuration file.

    Since Odoo 19, each unknown key of the [options] section logs "unknown
    option" as a WARNING, before any addon can declare it, and is stored as a
    raw string. The options are read from the [smile_upgrade] section, which
    Odoo ignores; the [options] section is still read for compatibility.
    """
    return _section_options.get(key, config.get(key, default))


def get_odoo_bool_option(key):
    return str2bool(get_odoo_option(key, False), default=False)


class ConfigManager(object):
    """Configuration Manager"""

    def __init__(self):
        self.options = {}
        self._get_default_options()
        self.load()

    def get(self, key, default=None):
        return self.options.get(key, default)

    def _get_default_options(self):
        upgrade_path = get_odoo_option("upgrades_path", "")
        if not upgrade_path:
            _logger.warning("Unspecified `upgrades_path` option "
                            "in Odoo configuration file")
            return
        if not os.path.exists(upgrade_path) or not os.path.isdir(upgrade_path):
            _logger.error("Specified `upgrades_path` option is not valid")
            return
        self.options["upgrades_path"] = upgrade_path
        config_file = os.path.join(upgrade_path, "upgrade.conf")
        if not os.path.exists(config_file) or not os.path.isfile(config_file):
            _logger.error(f"`upgrade.conf` doesn't exist in {upgrade_path}")
            return
        self.options["config_file"] = config_file
        self.options["force_reload_upgrade"] = get_odoo_bool_option(
            "force_reload_upgrade"
        )

    def load(self):
        config_file = self.options.get("config_file")
        if not config_file:
            return
        config = ConfigParser()
        try:
            config.read_file(open(config_file))
            self._check_config_file(config)
            for (key, value) in config.items("options"):
                if value in ("True", "False"):
                    value = safe_eval(value)
                self.options[key] = value
        except (IOError, NoSectionError):
            return

    def _check_config_file(self, config):
        for section in config.sections():
            if section != "options":
                _logger.warning("Only options section is taken into "
                                "account in upgrades configuration")


configuration = ConfigManager()
