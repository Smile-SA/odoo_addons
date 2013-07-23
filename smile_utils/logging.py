# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Smile (<http://www.smile.fr>).
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

from openerp.tools.func import wraps


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
