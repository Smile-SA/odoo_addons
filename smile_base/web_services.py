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
import os
import signal
import time
import uuid

from openerp.tools import config
from openerp.service import web_services
from openerp.service.web_services import objects_proxy, report_spool, wizard

_logger = logging.getLogger('openerp.smile_detective')
web_services._requests = {}
_requests = web_services._requests


def smile_detective(min_delay):  # min_delay in seconds
    def detective_log(dispatch_func):
        def detective_dispatch(self, method, params):
            pid = uuid.uuid4()
            db, uid = params[0:2]
            param_str = repr(params[3:])
            start = time.time()
            _requests[pid] = (db, uid, method, param_str, start)
            try:
                result = dispatch_func(self, method, params)
            finally:
                del _requests[pid]
            delay = time.time() - start
            if delay > min_delay:
                msg = u"WS_DB:%s WS_UID:%s WS_METHOD:%s WS_PARAMS:%s WS_TIMER:%s" % (db, uid, method, param_str, delay * 1000.0,)
                # WS_TIMER in milliseconds
                _logger.info(msg)
            return result
        return detective_dispatch
    return detective_log


objects_proxy.dispatch = smile_detective(config.get('log_service_object', 0.500))(objects_proxy.dispatch)
report_spool.dispatch = smile_detective(config.get('log_service_report', 0.500))(report_spool.dispatch)
wizard.dispatch = smile_detective(config.get('log_service_wizard', 0.500))(wizard.dispatch)

native_dumpstacks = signal.getsignal(signal.SIGQUIT)


def smile_dumpstacks(sig, frame):
    _logger.info("\n".join(map(str, _requests.values())))
    native_dumpstacks(sig, frame)

if os.name == 'posix':
    signal.signal(signal.SIGQUIT, smile_dumpstacks)
