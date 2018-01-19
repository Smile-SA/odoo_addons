# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>).
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

import datetime
import traceback


def add_timing(original_method):
    def new_method(self, msg):
        delay = datetime.datetime.now() - self._logger_start
        msg += " after %sh %smin %ss" % tuple(str(delay).split(':'))
        return original_method(self, msg)
    return new_method


def add_trace(original_method):
    def new_method(self, msg):
        stack = traceback.format_exc()
        stack = stack.replace('%', '%%')
        msg += '\n%s' % stack.decode('utf-8')
        return original_method(self, msg)
    return new_method
