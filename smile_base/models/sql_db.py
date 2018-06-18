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

import traceback

from odoo.sql_db import Cursor, _logger

native_execute = Cursor.execute


@Cursor.check
def execute(self, query, params=None, log_exceptions=None):
    try:
        return native_execute(self, query, params, log_exceptions)
    except Exception as e:
        _logger.error('Traceback (most recent call last):\n' + ''.join(
            traceback.format_stack()))
        raise


Cursor.execute = execute
