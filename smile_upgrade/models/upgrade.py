import importlib.util
import logging
import os
import psycopg2

from odoo import api, sql_db, SUPERUSER_ID, tools
from odoo.exceptions import UserError
import odoo.modules as addons
from odoo.tools import parse_version
from odoo.tools.func import lazy_property
from odoo.tools.safe_eval import safe_eval

from .config import configuration as upgrade_config

_logger = logging.getLogger(__package__)


class UpgradeManager(object):
    """Upgrade Manager
    * Compare code and database versions
    * Get upgrades to apply to database
    """

    def __init__(self, db_name):
        self.db_name = db_name
        self.db = sql_db.db_connect(db_name)
        self.cr = self.db.cursor()
        self.cr._cnx.autocommit = True
        self.force_reload = self._get_force_reload_param()
        self.upgrades = self._get_upgrades()
        self.modules_to_upgrade = list(set(sum(
            [upgrade.modules_to_upgrade for upgrade in self.upgrades], [])))
        self.modules_to_install_at_creation = self.upgrades and \
            self.upgrades[-1].modules_to_install_at_creation or []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.cr.commit()
        self.cr.close()

    @lazy_property
    def db_in_creation(self):
        self.cr.execute("SELECT relname FROM pg_class "
                        "WHERE relname='ir_config_parameter'")
        if self.cr.rowcount:
            return False
        return True

    @lazy_property
    def code_version(self):
        version = upgrade_config.get("version")
        if not version:
            _logger.warning(
                "Unspecified version in upgrades configuration file")
            version = "0"
        _logger.debug("code version: %s", version)
        return version

    @lazy_property
    def db_version(self):
        if self.db_in_creation:
            return "0"
        self.cr.execute("SELECT value FROM ir_config_parameter "
                        "WHERE key = 'code.version' LIMIT 1")
        version = self.cr.fetchone()
        if not version:
            _logger.warning("Unspecified version in database")
        version = version and version[0] or "0"
        _logger.debug("database version: %s", version)
        return version

    def set_db_version(self):
        params = (SUPERUSER_ID, str(self.code_version))
        self.cr.execute("SELECT value FROM ir_config_parameter "
                        "WHERE key = 'code.version' LIMIT 1")
        if not self.cr.rowcount:
            query = """INSERT INTO ir_config_parameter
               (create_date, create_uid, key, value)
               VALUES (now() at time zone 'UTC', %s, 'code.version', %s)"""
        else:
            query = """UPDATE ir_config_parameter
                SET (write_date, write_uid, value) =
                (now() at time zone 'UTC', %s, %s)
                WHERE key = 'code.version'"""
        self.cr.execute(query, params)
        _logger.debug("database version updated to %s", self.code_version)

    def _try_lock(self, warning=None):
        try:
            self.cr.execute("SELECT value FROM ir_config_parameter "
                            "WHERE key = 'code.version' FOR UPDATE NOWAIT",
                            log_exceptions=False)
        except psycopg2.OperationalError:
            # INFO: Early rollback to allow translations
            # to work for the user feedback
            self.cr.rollback()
            if warning:
                raise UserError(warning)
            raise

    def _get_force_reload_param(self):
        return upgrade_config.get("force_reload_upgrade")

    def _get_upgrades(self):
        upgrades_path = upgrade_config.get("upgrades_path")
        if not upgrades_path:
            return []
        if not self.db_in_creation:
            self._try_lock("Upgrade in progress")
        upgrades = self._get_upgrades_list(upgrades_path)
        upgrades.sort(key=lambda upgrade: upgrade.version)
        if upgrades and self.db_in_creation:
            upgrades = upgrades[-1:]
        return upgrades

    def _get_upgrades_list(self, upgrades_path):
        upgrades = []
        for dirname in os.listdir(upgrades_path):
            dir_path, file_path = self._get_upgrade_file(
                upgrades_path, dirname)
            if not dir_path or not file_path:
                continue
            if upgrade := self._get_upgrade(dir_path, file_path):
                upgrades.append(upgrade)
        return upgrades

    def _get_upgrade_file(self, upgrades_path, dirname):
        dir_path = os.path.join(upgrades_path, dirname)
        if not os.path.isdir(dir_path):
            return False, False
        file_path = os.path.join(dir_path, "__upgrade__.py")
        if dir_path and not os.path.exists(file_path):
            _logger.warning(f"{file_path} doesn't exist")
            return False, False
        elif not os.path.isfile(file_path):
            _logger.warning(u"%s is not a file", file_path)
            return False, False

        return dir_path, file_path

    def _get_upgrade(self, dir_path, file_path):
        with open(file_path) as upgrade_file:
            upgrade_infos = safe_eval(upgrade_file.read())
            try:
                upgrade = Upgrade(dir_path, upgrade_infos)
                if (not upgrade.databases or self.db_name in upgrade.databases
                    ) and parse_version(self.db_version) \
                    < parse_version(upgrade.version) \
                    <= parse_version(self.code_version) \
                    or (self.force_reload
                        and upgrade.version == self.code_version):
                    return upgrade
            except Exception as e:
                _logger.error(
                    "%s is not valid: %s", file_path, repr(e))
        return False

    def pre_load(self):
        with self.db.cursor() as cr:
            for upgrade in self.upgrades:
                upgrade.load_files(cr, "pre-load")

    def post_load(self):
        with self.db.cursor() as cr:
            for upgrade in self.upgrades:
                upgrade.load_files(cr, "post-load")

    def reload_translations(self):
        languages = []
        for upgrade in self.upgrades:
            languages += upgrade.translations_to_reload
        if languages:
            with self.db.cursor() as cr:
                context = {"overwrite": True}
                env = api.Environment(cr, SUPERUSER_ID, context)
                lang_ids = env["res.lang"].search(
                    [("code", "in", languages)]).ids
                env["base.language.install"].create(
                    {"lang_ids": [(6, 0, lang_ids)]}).lang_install()


class Upgrade(object):
    """Upgrade
    * Pre-load: accept only .sql files
    * Post-load: accept .sql, .csv, .xml and .py files
    """

    def __init__(self, dir_path, infos):
        self.dir_path = dir_path
        for k, v in infos.items():
            if k == "version":
                v = v or "0"
            setattr(self, k, v)

    def __getattr__(self, key):
        default_values = {
            "version": "",
            "databases": [],
            "translations_to_reload": [],
            "modules_to_upgrade": [],
            "modules_to_install_at_creation": [],
            "pre-load": [],
            "post-load": [],
        }
        if key not in self.__dict__ and key not in default_values:
            raise AttributeError(
                f"`{self.__class__.__name__}` object has no attribute `{key}`")
        return self.__dict__.get(key) or default_values.get(key)

    def _py_import(self, cr, f_obj):
        env = api.Environment(cr, SUPERUSER_ID, {})
        module_name = os.path.splitext(os.path.basename(f_obj.name))[0]
        spec = importlib.util.spec_from_file_location(module_name, f_obj.name)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.post_load_hook(env)

    def _sql_import(self, cr, f_obj):
        for query in f_obj.read().split(";"):
            clean_query = " ".join(query.split())
            if clean_query:
                cr.execute(clean_query)

    def _import_file(self, cr, mode, f_obj, module):
        __, ext = os.path.splitext(f_obj.name)
        if ext == ".sql":
            self._sql_import(cr, f_obj)
        elif mode == "post-load":
            if ext == ".py":
                self._py_import(cr, f_obj)
            elif ext == ".csv":
                tools.convert_csv_import(
                    cr, module, fname=f_obj.name, csvcontent=f_obj.read(),
                    mode="upgrade")
            elif ext == ".xml":
                tools.convert_xml_import(
                    cr, module, xmlfile=f_obj, mode="upgrade")
        else:
            _logger.error(
                "%s extension is not supported in upgrade %sing", ext, mode)
            pass

    def load_files(self, cr, mode):
        def format_files_list(f):
            if isinstance(f, tuple):
                return f[0], len(f) == 2 and f[1] or "raise"
            return f, "raise"
        _logger.debug("%sing %s upgrade...", mode, self.version)
        files_list = getattr(self, mode, [])
        for fname, error_management in map(format_files_list, files_list):
            filepath, module = self._prepare_file_import(fname)
            with open(filepath) as f_obj:
                _logger.info("importing %s file...", fname)
                cr.execute("SAVEPOINT smile_upgrades")
                try:
                    self._import_file(cr, mode, f_obj, module)
                    _logger.info("%s successfully imported", fname)
                except Exception as e:
                    self._manage_file_import_errors(
                        error_management, cr, fname, e)

    def _prepare_file_import(self, fname):
        f_name = fname.replace("/", os.path.sep)
        filepath = os.path.join(self.dir_path, f_name)
        module = "base"
        if not os.path.exists(filepath):
            for adp in addons.module.ad_paths:
                fp = os.path.join(adp, f_name)
                if os.path.exists(fp):
                    module = fname.split("/")[0]
                    break
            else:
                raise ValueError("No such file: %s", fp)
        return filepath, module

    def _manage_file_import_errors(self, error_management, cr, fname, e):
        if error_management == "rollback_and_continue":
            cr.execute("ROLLBACK TO SAVEPOINT smile_upgrades")
            _logger.warning("%s import rollbacking: %s", fname, e)
        elif error_management == "raise":
            raise e
        elif error_management != "not_rollback_and_continue":
            _logger.error(
                "%s value not supported in error management",
                error_management)
