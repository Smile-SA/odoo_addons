# -*- coding: utf-8 -*-

######################
# Log storage format #
######################
#
# RPC calls sequence
# c:s => integer
#
# Cumulative calls time by model.method
# c:t:<db>:<date@time> => sorted set
#   (<model>:<method>, tm)
#
# Cumulative calls number by model.method
# c:n:<db>:<date@time> => sorted set
#   (<model>:<method>, nb) 
#
# RPC calls
# c:x:<call_id>:<db>:<date@time>:<model>:<method>:<uid> => hash
#   tm => call time (in seconds)
#   db_tm => sql queries time (in seconds)
#   db_nb => sql queries number
#   args => params (only vals keys if method is create or write)
#   res => response (only if method is create)
#
# Python profiling
# c:p:<call_id> => string
#
# SQL requests
# c:q:<call_id> => sorted set
#   (table, statement, request time in seconds)

from datetime import datetime
from functools import partial
import logging
import re
import redis
from threading import local
import time

import openerp
from openerp.tools import config
from openerp.tools.func import wraps

from .misc import print_args

_logger = logging.getLogger(__name__)

SQL_REGEX = {
    'select': re.compile('SELECT .* FROM "([a-z_]+)".*'),
    'insert': re.compile('INSERT INTO "([a-z_]+)" .*'),
    'update': re.compile('UPDATE "([a-z_]+)" SET .*'),
    'delete': re.compile('DELETE FROM "([a-z_]+)".*'),
}


def secure(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            _logger.error('%s failed' % func.__name__)
    return wrapper


def only_if_active(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.active:
            return False
        return func(self, *args, **kwargs)
    return wrapper


class ThreadLog(local):
    inst = None


class ThreadSingleton(type):
    def __call__(cls, *args, **kwargs):
        if ThreadLog.inst is None:
            ThreadLog.inst = super(ThreadSingleton, cls).__call__(*args, **kwargs)
        return ThreadLog.inst


class PerfLogger(object):
    __metaclass__ = ThreadSingleton

    def __init__(self):
        self.redis = None
        self.redis_url = config.get_misc('perf', 'redis_url')
        if not self.redis_url:
            _logger.warning('No Redis URL specified in Odoo config file in section perf')
        else:
            self.redis = redis.from_url(self.redis_url)
            if not self.is_alive():
                self.redis = None
        self.id = None

    def is_alive(self):
        try:
            active = self.redis.ping()
            if not active:
                _logger.warning('Redis %s is inactive' % self.redis_url)
            return active
        except redis.exceptions.ConnectionError, e:
            _logger.error('Invalid Redis URL: %s' % e)
            return False

    @property
    def active(self):
        return self.id is not None

    def _sequence_key(self):
        return 'c:s'

    def _key(self, pattern):
        return pattern % self.__dict__

    def _log_cumulative_tm_key(self):
        return self._key('c:t:%(db)s:%(datetime)s')

    def _log_cumulative_nb_key(self):
        return self._key('c:n:%(db)s:%(datetime)s')

    def _log_call_key(self):
        return self._key('c:x:%(db)s:%(datetime)s:%(model)s:%(method)s:%(uid)s:%(id)s')

    def _log_profile_key(self):
        return self._key('c:p:%(id)s')

    def _log_query_key(self):
        return self._key('c:q:%(id)s')

    @secure
    def on_enter(self, cr, uid, model, method):
        if self.redis:
            self._check = partial(openerp.registry(cr.dbname).get('ir.logging.rule').check,
                                  cr, uid, model, method)
            if self._check():
                self.start = time.time()
                self.cr = cr
                self.db = cr.dbname
                self.uid = uid
                self.model = model
                self.method = method
                self.datetime = datetime.fromtimestamp(self.start).strftime('%Y-%m-%d@%H:%M:%S.%f')
                key = self._sequence_key()
                self.id = self.redis.incrby(key)

    @secure
    def on_leave(self):
        self.id = None

    @secure
    @only_if_active
    def check(self, log_python=False, log_sql=False):
        return self._check(log_python, log_sql)

    def _format_args(self, args, kwargs):
        # Hide values passed to create new record or update ones
        if self.method in ('create', 'write'):
            if len(args) > 1:
                for k in args[1]:
                    args[1][k] = '*'
            else:
                for field in ('values', 'vals'):
                    for k in (kwargs.get(field) or {}):
                        kwargs[field][k] = '*'
        return print_args(*args, **kwargs)

    def _format_res(self, res):
        if self.method != 'create':
            return '***'
        return res

    @secure
    @only_if_active
    def log_call(self, args, kwargs, res):
        tm = time.time() - self.start
        value = '%s:%s' % (self.model, self.method)
        key = self._log_cumulative_tm_key()
        self.redis.zincrby(key, value, tm)
        key = self._log_cumulative_nb_key()
        self.redis.zincrby(key, value, 1)
        key = self._log_call_key()
        self.redis.hmset(key, {
            'tm': tm,
            'args': self._format_args(args, kwargs),
            'res': self._format_res(res),
        })

    @secure
    @only_if_active
    def log_db_stats(self, delay):
        key = self._log_call_key()
        self.redis.hincrby(key, 'db_nb')
        self.redis.hincrbyfloat(key, 'db_tm', delay)

    @secure
    @only_if_active
    def log_profile(self, stats):
        key = self._log_profile_key()
        self.redis.set(key, stats)  # TODO: replace by a list

    def _parse_query(self, query):
        for statement, pattern in SQL_REGEX.iteritems():
            m = pattern.match(query, flags=re.IGNORECASE)
            if m:
                return m.group(1), statement
        return None, None

    @secure
    @only_if_active
    def log_query(self, query, delay):
        key = self._log_query_key()
        table, statement = self._parse_query(query)
        if table and statement:
            value = '%s:%s' % (table, statement)
            self.redis.zincrby(key, value, delay)
