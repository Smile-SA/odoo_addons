# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import registry


class SmileDBHandler(logging.Handler):

    def __init__(self, level=logging.NOTSET):
        logging.Handler.__init__(self, level)
        self._dbname_to_cr = {}

    def _get_cursor(self, dbname):
        cr = self._dbname_to_cr.get(dbname)
        if not cr or (cr and cr.closed):
            cr = registry(dbname).cursor()
            cr.autocommit(True)
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

        request = """INSERT INTO smile_log
        (log_date, log_uid, model_name, res_id, pid, level, message)
        VALUES (now() at time zone 'UTC', %s, %s, %s, %s, %s, %s)"""
        params = (uid, model_name, res_id, pid, record.levelname, record.msg,)

        try:
            cr.execute(request, params)
        except Exception:
            # retry
            cr = self._get_cursor(dbname)
            cr.execute(request, params)
        return True

    def close(self):
        logging.Handler.close(self)
        for cr in self._dbname_to_cr.values():
            try:
                cr.execute(
                    "INSERT INTO smile_log "
                    "(log_date, log_uid, model_name, "
                    "res_id, pid, level, message) "
                    "VALUES (now() at time zone 'UTC', 0, '', "
                    "0, 0, 'INFO', 'Odoo server stopped')")
            finally:
                cr.close()
        self._dbname_to_cr = {}


logging.getLogger('smile_log').addHandler(SmileDBHandler())
