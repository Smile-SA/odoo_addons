# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import datetime
import logging

from odoo.modules.registry import RegistryManager

from .misc import add_timing, add_trace


class SmileDBLogger:

    def __init__(self, dbname, model_name, res_id, uid=0):
        assert isinstance(uid, (int, long)), 'uid should be an integer'
        self._logger = logging.getLogger('smile_log')

        db = RegistryManager.get(dbname)._db
        pid = 0

        try:
            cr = db.cursor()
            cr.autocommit(True)
            cr.execute("select relname from pg_class where relname='smile_log_seq'")
            if not cr.rowcount:
                cr.execute("create sequence smile_log_seq")
            cr.execute("select nextval('smile_log_seq')")
            res = cr.fetchone()
            pid = res and res[0] or 0
        finally:
            cr.close()

        self._logger_start = datetime.datetime.now()
        self._logger_args = {'dbname': dbname, 'model_name': model_name, 'res_id': res_id, 'uid': uid, 'pid': pid}

    @property
    def pid(self):
        return self._logger_args['pid']

    def setLevel(self, level):
        self._logger.setLevel(level)

    def getEffectiveLevel(self):
        return self._logger.getEffectiveLevel()

    def debug(self, msg):
        self._logger.debug(msg, self._logger_args)

    def info(self, msg):
        self._logger.info(msg, self._logger_args)

    def warning(self, msg):
        self._logger.warning(msg, self._logger_args)

    def log(self, msg):
        self._logger.log(msg, self._logger_args)

    @add_trace
    def error(self, msg):
        self._logger.error(msg, self._logger_args)

    @add_trace
    def critical(self, msg):
        self._logger.critical(msg, self._logger_args)

    @add_trace
    def exception(self, msg):
        self._logger.exception(msg, self._logger_args)

    @add_timing
    def time_info(self, msg):
        self._logger.info(msg, self._logger_args)

    @add_timing
    def time_debug(self, msg):
        self._logger.debug(msg, self._logger_args)
