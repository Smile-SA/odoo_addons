# -*- coding: utf-8 -*-

######################
# Log storage format #
######################
#
# RPC calls
# c:<db>:<model>:<method>:<date@time>:<uid>:<call_id> => hash
#   tm => call time
#   db_tm => sql queries time
#   db_nb => sql queries number
#   args => params (only vals keys if method is create or write)
#   res => response (only if method is create)
#
# RPC calls sequence
# c:n => integer
#
# Python profiling
# c:p:<db>:<model>:<method>:<date@time>:<uid>:<call_id> => list
#   (method,*stats)
#
# SQL requests
# c:q:<db>:<model>:<method>:<date@time>:<uid>:<call_id> => list
#   (query, tm)
#

from datetime import datetime
from functools import partial
import logging
import redis
from threading import local
import time

import openerp
from openerp.tools import config
from openerp.tools.func import wraps

from .misc import print_args

_logger = logging.getLogger(__name__)


def secure(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            _logger.error('%s failed' % func.__name__)
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
        self.key = None
        self.redis = None
        self.redis_url = config.get_misc('perf', 'redis_url')
        if not self.redis_url:
            _logger.warning('No Redis URL specified in Odoo config file in section perf')
        else:
            self.redis = redis.from_url(self.redis_url)
            if not self.is_alive():
                self.redis = None

    def is_alive(self):
        try:
            active = self.redis.ping()
            if not active:
                _logger.warning('Redis %s is inactive' % self.redis_url)
            return active
        except redis.exceptions.ConnectionError, e:
            _logger.error('Invalid Redis URL: %s' % e)
            return False

    _key_pattern = 'c:%(db)s:%(model)s:%(method)s:%(uid)s:%(datetime)s:%(id)s'

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
                self.id = self.redis.incrby('c:n')
                self.key = self._key_pattern % self.__dict__

    @secure
    def on_leave(self):
        self.key = None

    @secure
    def check(self, log_python=False, log_sql=False):
        if not self.key:
            return False
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
    def log_call(self, args, kwargs, res):
        if self.key:
            self.redis.hmset(self.key, {
                'tm': time.time() - self.start,
                'args': self._format_args(args, kwargs),
                'res': self._format_res(res),
            })

    @secure
    def log_db_stats(self, delay):
        if self.key:
            self.redis.hincrby(self.key, 'db_nb')
            self.redis.hincrbyfloat(self.key, 'db_tm', delay)

    @secure
    def log_profile(self, stats):
        if self.key:
            key = 'c:p:%s' % self.key[2:]
            self.redis.set(key, stats)  # TODO: replace by a list

    @secure
    def log_query(self, query, delay):
        if self.key:
            key = 'c:q:%s' % self.key[2:]
            self.redis.rpush(key, (query, delay))
