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

import logging
import os

from openerp import sql_db, tools

from config import configuration as config

_logger = logging.getLogger('upgrades')


class UpgradeManager(object):
    """Upgrade Manager"""

    def __init__(self, db_name):
        self.db_name = db_name
        db = sql_db.db_connect(db_name)
        self.cr = db.cursor()
        self.code_version = self._get_code_version()
        self.db_version = self._get_db_version()
        self.upgrades = self._get_upgrades()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.cr.close()

    def _get_code_version(self):
        version = config.get('version')
        if not version:
            _logger.warning('Unspecified version in upgrades configuration file')
        _logger.debug('code version: %s', version)
        return version

    def _get_db_version(self):
        self.cr.execute("SELECT value FROM ir_config_parameter WHERE key = 'code.version' LIMIT 1")
        param = self.cr.fetchone()
        if not param:
            self.cr.execute("INSERT INTO ir_config_parameter (key, value) VALUES ('code.version', '')")
            _logger.warning('Unspecified version in database')
            return ''
        _logger.debug('database version: %s', param[0])
        return param[0]

    def _get_upgrades(self):
        upgrades_path = config.get('upgrades_path')
        if not upgrades_path:
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
                        upgrade_info = eval(f.read())
                        if not isinstance(upgrade_info, dict):
                            _logger.error("%s is not valid. It must be a dictionary", file_path)
                            continue
                        databases = upgrade_info.get('databases', [])
                        if (not databases or self.db_name in databases) \
                                and self.db_version < upgrade_info.get('version') <= self.code_version:
                            upgrades.append(Upgrade(self.cr, dir_path, upgrade_info))
                    except:
                        _logger.error('%s is not evaluable', file_path)
        return sorted(upgrades, key=lambda upgrade: upgrade.get('version'))


class Upgrade(object):

    def __init__(self, cr, dir_path, infos):
        self.cr = cr
        self.dir_path = dir_path
        self.infos = infos

    def get(self, key, default=None):
        return self.infos.get(key, default)

    def _set_db_version(self):
        self.cr.execute("UPDATE ir_config_parameter SET value = %s WHERE key = 'code.version'", (self.get('version', ''),))
        self.cr.commit()

    def _sql_import(self, f_obj):
        for query in f_obj.read().split(';'):
            clean_query = ' '.join(query.split())
            if clean_query:
                self.cr.execute(clean_query)

    def _load_files(self, mode):
        _logger.debug('%sing %s upgrade...', (mode, self.get('version')))
        for fname in (self.get(mode) or []):
            fp = os.path.join(self.dir_path, fname.replace('/', os.path.sep))
            if not os.path.exists(fp):
                _logger.error("%s doesn't exist", fp)
                pass
            root, ext = os.path.splitext(fp)
            with open(fp) as f_obj:
                _logger.debug('importing %s file...', fname)
                if ext == '.sql':
                    self._sql_import(f_obj)
                elif mode != 'pre-load' and ext == '.yml':
                    tools.convert_yaml_import(self.cr, 'base', f_obj)
                else:
                    _logger.error('%s extension is not supported in upgrade %sing' % (ext, mode))
                    continue
                _logger.debug('%s successfully imported', fname)

    def pre_load(self):
        _logger.info('loading %s upgrade...', self.get('version'))
        self._load_files('pre-load')

    def post_load(self):
        self._load_files('post-load')
        self._set_db_version()
        _logger.info('%s upgrade successfully loaded', self.get('version'))
