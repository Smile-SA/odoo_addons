# -*- coding: utf-8 -*-

######################
# Log storage format #
######################
#
# RPC calls
# c:<db>:<model>:<method>:<date@time>:<uid>:<call_id> => hash
#   rpctype (useful?)
#   sessionid (useful?)
#   tm => call time
#   db_tm => sql queries time
#   db_nb => sql queries number
#   args => params (TODO: only vals keys if method is create or write)
#   err => true or false
#   res => response (TODO: only if method is create)
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
import logging
import redis
from threading import local
import time

from openerp.http import request
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


class Logger(object):
    __metaclass__ = ThreadSingleton

    def __init__(self):
        self.key = None
        self.redis = None
        self.redis_url = config.get_misc('perf', 'redis_url')
        if not self.redis_url:
            _logger.warning('No Redis URL specified in Odoo config file')
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
    def on_enter(self, model, method):
        if self.redis:
            self.cr = request.cr
            self.uid = request.uid
            if request.registry('ir.logging.rule').check(self.cr, self.uid, model, method):
                self.start = time.time()
                self.db = request.db
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
        args = self.cr, self.uid, self.model, self.method, log_python, log_sql
        return request.registry.get('ir.logging.rule').check(*args)

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
            self._filter_args(args, kwargs)
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
