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
import threading
import traceback

import pooler
import tools

class SmileDBHandler(logging.Handler):

    def __init__(self, log_model, level=logging.NOTSET):
        logging.Handler.__init__(self, level)
        self._dbname_to_cr = {}
        self._log_model = log_model

    def emit(self, record):
        dbname = getattr(threading.currentThread(), 'dbname', '')
        db, pool = pooler.get_db_and_pool(dbname, pooljobs=False)
        cr = self._dbname_to_cr.get(dbname, False)
        if not cr:
            cr = self._dbname_to_cr[dbname] = db.cursor()

        parent_id, pid, uid = False, '', False
        if record.args and isinstance(record.args, dict):
            parent_id = record.args.get('parent_id', False)
            pid = record.args.get('pid', '')
            uid = record.args.get('uid', False)

        if uid and pool.get('res.users').exists(cr, 1, uid):
            pool.get(self._log_model).create(cr, uid, {
                'parent_id': parent_id,
                'pid': pid,
                'level': record.levelname,
                'message': record.msg,
            })
        else:
            cr.execute("INSERT INTO %s (create_date, parent_id, pid, level, message) VALUES (now(), %s, %s, %s)",
                       (pool.get(self._log_model)._table,
                        parent_id,
                        pid,
                        record.levelname,
                        record.msg,))
        cr.commit()
        return True

    def close(self):
        logging.Handler.close(self)
        for cr in self._dbname_to_cr.values():
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
        msg += '\n%s' % stack
        return original_method(self, msg)
    return new_method

class SmileDBLogger():

    def __init__(self, logger_name, parent_id, uid=0, pid=''):
        assert isinstance(uid, (int, long)), 'uid should be an integer'
        self._logger = logging.getLogger(logger_name)
        self._parent_id = parent_id
        self._uid = uid
        self._pid = pid
        self._logger_start = datetime.datetime.now()
        self._logger_args = {'parent_id': self._parent_id, 'uid': self._uid, 'pid': pid}

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
