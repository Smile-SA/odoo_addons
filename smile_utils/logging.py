# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2013 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import cProfile

from openerp.tools.func import wraps


def profile_this(fn):
    def profiled_fn(*args, **kwargs):
        fpath = fn.__name__ + '.profile'
        prof = cProfile.Profile()
        ret = prof.runcall(fn, *args, **kwargs)
        prof.dump_stats(fpath)
        return ret
    return profiled_fn


def timeme(logger, message, arg_to_display_indexes=None, log_level='info'):
    def wrap(original_method):
        @wraps(original_method)
        def wrapper(*args, **kwargs):
            time_start = time.time()
            msg = '[%s] %s' % (time_start, message)
            if arg_to_display_indexes:
                msg += ': %s' % ', '.join([str(args[i]) for i in arg_to_display_indexes])
            getattr(logger, log_level)(msg)
            res = original_method(*args, **kwargs)
            time_stop = time.time()
            getattr(logger, log_level)('[%s] Execution time : %s' % (time_start, time_stop - time_start))
            return res
        return wrapper
    return wrap


def smile_detective(min_delay):
    """
    Put this decorator on the dispatch() method in the openerp/service/web_services.py file. Eg:

        === modified file 'openerp/service/web_services.py'
        --- openerp/service/web_services.py 2013-03-18 14:41:56 +0000
        +++ openerp/service/web_services.py 2013-07-23 10:27:02 +0000
        @@ -603,10 +603,27 @@
                 return sql_db.sql_counter


         class objects_proxy(netsvc.ExportService):
             def __init__(self, name="object"):
                 netsvc.ExportService.__init__(self,name)

        +    @smile_detective(0.5)
             def dispatch(self, method, params):
                 (db, uid, passwd ) = params[0:3]

    """
    def detective_log(dispatch_func):
        def detective_dispatch(self, method, params):
            db, uid = params[0:2]
            param_str = repr(params[3:])
            start = time.time()
            result = dispatch_func(self, method, params)
            delay = time.time() - start
            if delay > min_delay:
                msg = u"WS_DB:%s WS_UID:%s WS_PARAMS:%s WS_TIMER:%s" % (db, uid, param_str, delay * 1000.0,)
                logging.getLogger('smile_detective').info(msg)
            return result
        return detective_dispatch
    return detective_log
