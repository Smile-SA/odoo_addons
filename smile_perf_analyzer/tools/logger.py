# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime
from functools import partial
import logging
import re
import six
import sys
import threading
import time
import traceback

from odoo import api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.tools.func import wraps

from .exceptions import get_exception_message
from .misc import print_args
from .sql import perf_cursor

if sys.version_info > (3,):
    long = int

_logger = logging.getLogger(__name__)

SQL_REGEX = {
    'select': re.compile('SELECT .* FROM "([a-z_]+)".*', flags=re.IGNORECASE),
    'insert': re.compile('INSERT INTO "([a-z_]+)" .*', flags=re.IGNORECASE),
    'update': re.compile('UPDATE "([a-z_]+)" SET .*', flags=re.IGNORECASE),
    'delete': re.compile('DELETE FROM "([a-z_]+)".*', flags=re.IGNORECASE),
}


def secure(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            _logger.error('%s failed: %s' % (func.__name__, e))
    return wrapper


def only_if_active(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.active:
            return False
        return func(self, *args, **kwargs)
    return wrapper


class ThreadSingleton(type):
    def __call__(cls, *args, **kwargs):
        current_thread = threading.current_thread()
        if not getattr(current_thread, 'perf_logger', None):
            current_thread.perf_logger = super(ThreadSingleton, cls). \
                __call__(*args, **kwargs)
        return current_thread.perf_logger


@six.add_metaclass(ThreadSingleton)
class PerfLogger():

    def __init__(self):
        self.active = False
        self.recompute_min_duration = 0.0

    def reset(self):
        self.db_nb = 0
        self.db_tm = 0.0
        self.stats = ""
        self.db_stats = {}
        self.slow_queries = []
        self.slow_recomputation = []

    @secure
    def on_enter(self, cr, uid, path, model, method):
        self.env = api.Environment(cr, uid, {})
        if 'ir.logging.perf.rule' in self.env.registry.models:
            PerfRule = self.env['ir.logging.perf.rule']
            check = partial(PerfRule.check, path, model, method)
            if check():
                self.active = True
                self.db = cr.dbname
                self.uid = uid
                self.model = model
                self.method = method
                self.path = path
                self.reset()
                self.log_python = check(log_python=True)
                self.log_sql = check(log_sql=True)
                min_duration = partial(
                    PerfRule.get_min_duration, path, model, method)
                self.min_duration = min_duration()
                self.sql_min_duration = min_duration('sql')
                self.recompute_min_duration = min_duration('recompute')
                self.ts = time.time()

    @secure
    def on_leave(self):
        self.active = False
        self.reset()

    def _format_args(self, args, kwargs):
        args = args or []
        kwargs = kwargs or {}
        if 'args' in kwargs:
            args = kwargs['args']
            kwargs = kwargs.get('kwargs') or {}
        # Hide values passed to create new record or update ones
        if self.method in ('create', 'write', 'onchange'):
            if len(args) > 1:
                for k in args[1]:
                    args[1][k] = '*'
            else:
                for field in ('values', 'vals'):
                    for k in (kwargs.get(field) or {}):
                        kwargs[field][k] = '***'
        return print_args(*args, **kwargs)

    def _format_res(self, res):
        if self.method in ('create', 'copy') or \
                isinstance(res, (bool, int, long, float)):
            return res
        return '***'

    @secure
    @only_if_active
    def log_call(self, args=None, kwargs=None, res='', err=''):
        tm = time.time() - self.ts
        if tm < self.min_duration:
            return
        vals = {
            'path': self.path,
            'date': datetime.fromtimestamp(self.ts).strftime(DATETIME_FORMAT),
            'uid': self.uid,
            'model': self.model,
            'method': self.method,
            'total_time': tm,
            'db_time': self.db_tm,
            'db_count': self.db_nb,
            'args': self._format_args(args, kwargs),
            'result': self._format_res(res),
            'error': get_exception_message(err),
            'stats': self.stats,
            'db_stats': repr(self.db_stats),
            'slow_queries': repr(self.slow_queries),
            'slow_recomputation': repr(self.slow_recomputation),
        }
        PerfLog = self.env['ir.logging.perf.log']
        updates = [('id', "nextval('%s')" % PerfLog._sequence)]
        for col in vals:
            field = PerfLog._fields[col]
            updates.append((col, field.column_format,
                            field.convert_to_column(vals[col], PerfLog)))
        columns = ', '.join('"%s"' % u[0] for u in updates)
        values = ', '.join(u[1] for u in updates)
        query = 'INSERT INTO ir_logging_perf_log (%s) VALUES (%s)' % \
            (columns, values)
        params = [u[2] for u in updates if len(u) > 2]
        with perf_cursor(self.db) as cr:
            cr.execute(query, tuple(params))

    @secure
    @only_if_active
    def log_db_stats(self, duration):
        self.db_nb += 1
        self.db_tm += duration

    @secure
    @only_if_active
    def log_profile(self, stats):
        self.stats = stats

    @staticmethod
    def parse_query(query):
        for statement, pattern in SQL_REGEX.items():
            m = pattern.match(query)
            if m:
                return m.group(1), statement
        return None, None

    @secure
    @only_if_active
    def log_query(self, query, duration):
        table, statement = self.parse_query(query)
        if table and statement:
            key = (table, statement)
            self.db_stats.setdefault(key, [0.0, 0])
            self.db_stats[key][0] += duration
            self.db_stats[key][1] += 1

    @secure
    @only_if_active
    def log_slow_query(self, query, duration):
        bt = ''.join(traceback.format_stack()[:-2])
        self.slow_queries.append((query, duration, bt))

    @secure
    @only_if_active
    def log_field_recomputation(self, model, field, records_nb, duration):
        self.slow_recomputation.append((model, field, duration, records_nb))
