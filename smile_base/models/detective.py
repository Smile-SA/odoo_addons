# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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

import logging
import time
import uuid

from odoo.http import WebRequest
from odoo.sql_db import Cursor
from odoo.tools import config

_logger = logging.getLogger('odoo.smile_detective')
_requests = {}


def smile_detective(min_delay):  # min_delay in seconds
    def detective_log(dispatch_func):
        def detective_dispatch(self, *args, **kwargs):
            pid = uuid.uuid4()
            db, uid = self.db, self.uid
            start = time.time()
            _requests[pid] = (db, uid, args, kwargs)
            try:
                result = dispatch_func(self, *args, **kwargs)
            finally:
                del _requests[pid]
            delay = time.time() - start
            if delay > min_delay:
                # WS_TIMER in milliseconds
                msg = u"WS_DB:%s WS_UID:%s WS_PARAMS:%s WS_TIMER:%s" % \
                      (db, uid, kwargs, delay * 1000.0)
                _logger.info(msg)
            return result
        return detective_dispatch
    return detective_log


def smile_sql_detective(min_delay):
    def detective_log(dispatch_func):
        def detective_execute(self, query, params=None, log_exceptions=True):
            start = time.time()
            result = dispatch_func(self, query, params, log_exceptions)
            delay = time.time() - start
            if delay > min_delay >= 0.0:
                _logger.info(u"SQL_BD:%s SQL_QUERY:%s SQL_PARAMS:%s SQL_TIMER:%s"
                             % (self.dbname, query.decode('utf-8'), params, delay * 1000.0,))
            return result
        return detective_execute
    return detective_log

Cursor.execute = smile_sql_detective(config.get('log_sql_request', 0.150))(Cursor.execute)
WebRequest._call_function = smile_detective(config.get('log_service_model', 0.300))(WebRequest._call_function)
