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

from openerp import sql_db, SUPERUSER_ID, tools
from openerp.netsvc import Service

from config import configuration as config

_logger = logging.getLogger('upgrades')


@contextmanager
def cursor(db, auto_commit=True):
    cr = db.cursor()
    try:
        yield cr
        if auto_commit:
            cr.commit()
    finally:
        cr.close()


class UpgradeManager(object):
    """Upgrade Manager
    * Compare code and database versions
    * Get upgrades to apply to database
    """

    def __init__(self, db_name):
        self.db_name = db_name
        self.db = sql_db.db_connect(db_name)
        self.cr = self.db.cursor()
        self.db_in_creation = self._get_db_in_creation()
        self.code_version = self._get_code_version()
        self.db_version = self._get_db_version()
        self.upgrades = self._get_upgrades()

    def _get_db_in_creation(self):
        self.cr.execute("SELECT relname FROM pg_class WHERE relname='ir_config_parameter'")
        if self.cr.rowcount:
            return False
        return True

    def _get_code_version(self):
        version = config.get('version')
        if not version:
            _logger.warning('Unspecified version in upgrades configuration file')
        _logger.debug('code version: %s', version)
        return version

    def _get_db_version(self):
        if self.db_in_creation:
            return ''
        self.cr.execute("SELECT value FROM ir_config_parameter WHERE key = 'code.version' LIMIT 1")
        param = self.cr.fetchone()
        if not param:
            with cursor(self.db) as cr:
                cr.execute("INSERT INTO ir_config_parameter (key, value) VALUES ('code.version', '')")
            _logger.warning('Unspecified version in database')
            return ''
        _logger.debug('database version: %s', param[0])
        return param[0]

    def _get_upgrades(self):
        upgrades_path = config.get('upgrades_path')
        if self.db_in_creation or not upgrades_path:
            return []
        upgrades = []
        for dir in os.listdir(upgrades_path):
            dir_path = os.path.join(upgrades_path, dir)
            if os.path.isdir(dir_path):
                file_path = os.path.join(dir_path, '__upgrade__.py')
                if not os.path.exists(file_path):
                    _logger.warning(u"%s doesn't exist", file_path)
                    continue
                if not os.path.isfile(file_path):
                    _logger.warning(u'%s is not a file', file_path)
                    continue
                with open(file_path) as f:
                    try:
                        upgrade_infos = eval(f.read())
                        upgrade = Upgrade(self.db, dir_path, upgrade_infos)
                        if (not upgrade.databases or self.db_name in upgrade.databases) \
                                and self.db_version < upgrade.version <= self.code_version:
                            upgrades.append(upgrade)
                    except:
                        _logger.error('%s is not valid', file_path)
        return sorted(upgrades, key=lambda upgrade: upgrade.version)


class Upgrade(object):
    """Upgrade
    * Pre-load: accept only .sql files
    * Post-load: accept .sql and .yml files
    """

    def __init__(self, db, dir_path, infos):
        self.db = db
        self.dir_path = dir_path
        for k, v in infos.iteritems():
            setattr(self, k, v)

    def __getattr__(self, key):
        default_values = {'version': '', 'databases': [], 'modules_to_upgrade': [],
                          'pre-load': [], 'post-load': []}
        if key not in self.__dict__ and key not in default_values:
            raise AttributeError("'%s' object has no attribute '%s'" % (self.__class__.__name__, key))
        return self.__dict__.get(key) or default_values.get(key)

    def _set_db_version(self):
        with cursor(self.db) as cr:
            cr.execute("UPDATE ir_config_parameter SET value = %s WHERE key = 'code.version'", (self.version,))

    def _sql_import(self, cr, f_obj):
        for query in f_obj.read().split(';'):
            clean_query = ' '.join(query.split())
            if clean_query:
                cr.execute(clean_query)

    def _load_files(self, cr, mode):
        _logger.debug('%sing %s upgrade...', (mode, self.version))
        for fname in getattr(self, mode, []):
            fp = os.path.join(self.dir_path, fname.replace('/', os.path.sep))
            if not os.path.exists(fp):
                _logger.error("%s doesn't exist", fp)
                pass
            root, ext = os.path.splitext(fp)
            with open(fp) as f_obj:
                _logger.info('importing %s file...', fname)
                if ext == '.sql':
                    self._sql_import(cr, f_obj)
                elif mode != 'pre-load' and ext == '.yml':
                    tools.convert_yaml_import(cr, 'base', f_obj)
                else:
                    _logger.error('%s extension is not supported in upgrade %sing' % (ext, mode))
                    continue
                _logger.info('%s successfully imported', fname)

    def _reset_services(self):
        for service in Service._services.keys():
            if service.startswith('report.'):
                del Service._services[service]

    def pre_load(self):
        _logger.info('loading %s upgrade...', self.version)
        with cursor(self.db) as cr:
            self._load_files(cr, 'pre-load')

    def post_load(self):
        with cursor(self.db) as cr:
            self._load_files(cr, 'post-load')
        self._set_db_version()
        self._reset_services()
        _logger.info('%s upgrade successfully loaded', self.version)

    def force_modules_upgrade(self, registry):
        uid = SUPERUSER_ID
        with cursor(self.db) as cr:
            registry.get('ir.module.module').update_list(cr, uid)
            module_obj = registry.get('ir.module.module')
            ids_to_install = module_obj.search(cr, uid, [('name', 'in', self.modules_to_upgrade),
                                                         ('state', 'in', ('uninstalled', 'to install'))])
            module_obj.button_install(cr, uid, ids_to_install)
            ids_to_upgrade = module_obj.search(cr, uid, [('name', 'in', self.modules_to_upgrade),
                                                         ('state', 'in', ('installed', 'to upgrade'))])
            module_obj.button_upgrade(cr, uid, ids_to_upgrade)
            cr.execute("UPDATE ir_module_module SET state = 'to upgrade' WHERE state = 'to install'")
        self._reset_services()
