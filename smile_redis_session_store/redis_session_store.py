# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Smile (<http://www.smile.fr>). All Rights Reserved
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

# Inspired by aek's Gist (<https://gist.github.com/aek/efb0f9dd8935471f9070>).


import cPickle
import werkzeug.contrib.sessions

from odoo import http, tools
from odoo.tools.func import lazy_property

SESSION_TIMEOUT = 60 * 60 * 24 * 7  # 1 weeks in seconds


def is_redis_session_store_activated():
    return tools.config.get('enable_redis')


try:
    import redis
except ImportError:
    if is_redis_session_store_activated():
        raise ImportError('Please install package python-redis: apt-get install python-redis')


class RedisSessionStore(werkzeug.contrib.sessions.SessionStore):

    def __init__(self, *args, **kwargs):
        super(RedisSessionStore, self).__init__(*args, **kwargs)
        self.expire = kwargs.get('expire', SESSION_TIMEOUT)
        self.key_prefix = kwargs.get('key_prefix', '')
        self.redis = redis.Redis(host=tools.config.get('redis_host', 'localhost'),
                                 port=int(tools.config.get('redis_port', 6379)),
                                 db=int(tools.config.get('redis_dbindex', 1)),
                                 password=tools.config.get('redis_pass', None))
        self._is_redis_server_running()

    def save(self, session):
        key = self._get_session_key(session.sid)
        data = cPickle.dumps(dict(session))
        self.redis.setex(name=key, value=data, time=self.expire)

    def delete(self, session):
        key = self._get_session_key(session.sid)
        self.redis.delete(key)

    def _get_session_key(self, sid):
        key = self.key_prefix + sid
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        return key

    def get(self, sid):
        key = self._get_session_key(sid)
        data = self.redis.get(key)
        if data:
            self.redis.setex(name=key, value=data, time=self.expire)
            data = cPickle.loads(data)
        else:
            data = {}
        return self.session_class(data, sid, False)

    def _is_redis_server_running(self):
        try:
            self.redis.ping()
        except redis.ConnectionError:
            raise redis.ConnectionError('Redis server is not responding')


if is_redis_session_store_activated():

    # Patch methods of openerp.http to use Redis instead of filesystem

    def session_gc(session_store):
        # Override to ignore file unlink because sessions are not stored in files
        pass

    http.session_gc = session_gc
    http.root.session_store = RedisSessionStore(session_class=http.OpenERPSession)
