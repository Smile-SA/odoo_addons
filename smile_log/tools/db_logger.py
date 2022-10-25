# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime
import logging
import sys

from odoo import registry

from .misc import add_timing, add_trace

if sys.version_info > (3,):
    long = int


class SmileDBLogger:

    def __init__(self, dbname, model_name, res_id, uid=0):
        assert isinstance(uid, (int, long)), 'uid should be an integer'
        self._logger = logging.getLogger('smile_log')

        pid = 0

        try:
            cr = registry(dbname).cursor()
            cr.autocommit(True)
            cr.execute(
                "select relname from pg_class "
                "where relname='smile_log_seq'")
            if not cr.rowcount:
                cr.execute("create sequence smile_log_seq")
            cr.execute("select nextval('smile_log_seq')")
            res = cr.fetchone()
            pid = res and res[0] or 0
        finally:
            cr.close()

        self._logger_start = datetime.datetime.now()
        self._logger_args = {
            'dbname': dbname, 'model_name': model_name,
            'res_id': res_id, 'uid': uid, 'pid': pid}

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
