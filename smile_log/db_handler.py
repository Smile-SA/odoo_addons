# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
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

import datetime
import logging
import traceback

import pooler


class SmileDBHandler(logging.Handler):

    def __init__(self, level=logging.NOTSET):
        logging.Handler.__init__(self, level)
        self._dbname_to_cr = {}

    def _get_cursor(self, dbname):
        cr = self._dbname_to_cr.get(dbname)
        if not cr or (cr and cr.closed):
            db, pool = pooler.get_db_and_pool(dbname, pooljobs=False)
            cr = db.cursor()
            self._dbname_to_cr[dbname] = cr
        return cr

    def emit(self, record):
        if not (record.args and isinstance(record.args, dict)):
            return False

        dbname = record.args.get('dbname', '')
        cr = self._get_cursor(dbname)

        res_id = record.args.get('res_id', 0)
        pid = record.args.get('pid', 0)
        uid = record.args.get('uid', 0)
        model_name = record.args.get('model_name', '')

        request = """INSERT INTO smile_log (log_date, log_uid, model_name, res_id, pid, level, message)
        VALUES (now(), %s, %s, %s, %s, %s, %s)"""
        params = (uid, model_name, res_id, pid, record.levelname, record.msg,)

        try:
            cr.execute(request, params)
        except Exception:
            # retry
            cr = self._get_cursor(dbname)
            cr.execute(request, params)

        cr.commit()

        return True

    def close(self):
        logging.Handler.close(self)
        for cr in self._dbname_to_cr.values():
            try:
                cr.execute("INSERT INTO smile_log (log_date, log_uid, model_name, res_id, pid, level, message) "
                           "VALUES (now(), 0, '', 0, 0, 'INFO', 'OpenERP server stopped')")
                cr.commit()
            finally:
                cr.close()
        self._dbname_to_cr = {}


def add_timing(original_method):
    def new_method(self, msg):
        delay = datetime.datetime.now() - self._logger_start
        msg += " after %sh %smin %ss" % tuple(str(delay).split(':'))
        return original_method(self, msg)
    return new_method


def add_trace(original_method):
    def new_method(self, msg):
        stack = traceback.format_exc()
        stack = stack.replace('%', '%%')
        msg += '\n%s' % stack
        return original_method(self, msg)
    return new_method


class SmileDBLogger():

    def __init__(self, dbname, model_name, res_id, uid=0):
        assert isinstance(uid, (int, long)), 'uid should be an integer'
        self._logger = logging.getLogger('smile_log')

        db, pool = pooler.get_db_and_pool(dbname, pooljobs=False)
        pid = 0
        try:
            cr = db.cursor()
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

logging.getLogger('smile_log').addHandler(SmileDBHandler())
