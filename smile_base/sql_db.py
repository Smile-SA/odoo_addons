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

from openerp.tools import config
from openerp.sql_db import Cursor

_logger = logging.getLogger('openerp.smile_detective')


def smile_sql_detective(min_delay):
    def detective_log(dispatch_func):
        def detective_execute(self, query, params=None, log_exceptions=True):
            start = time.time()
            result = dispatch_func(self, query, params, log_exceptions)
            delay = time.time() - start
            if delay > min_delay:
                _logger.info(u"SQL_BD:%s SQL_QUERY:%s SQL_PARAMS:%s SQL_TIMER:%s" % (self.dbname, query, params, delay * 1000.0,))
            return result
        return detective_execute
    return detective_log


Cursor.execute = smile_sql_detective(config.get('log_sql_request', 0.150))(Cursor.execute)
