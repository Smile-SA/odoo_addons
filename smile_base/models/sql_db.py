# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import traceback

from odoo.sql_db import Cursor, _logger


native_execute = Cursor.execute


def execute(self, query, params=None, log_exceptions=None):
    try:
        return native_execute(self, query, params, log_exceptions)
    except Exception as e:
        _logger.error(e)
        _logger.error('Traceback (most recent call last):\n' + ''.join(
            traceback.format_stack()))
        raise


Cursor.execute = execute
