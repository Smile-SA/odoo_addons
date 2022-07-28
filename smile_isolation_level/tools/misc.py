# -*- coding: utf-8 -*-
# (C) 2022 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from decorator import decorator

_logger = logging.getLogger(__name__)


def change_isolation_level(method=None, level=None):
    def _isolationLevel(method, self, *args, **kwargs):
        if level:
            _logger.info(
                'force postgresql isolation level to {}'.format(level))
            self._cr._cnx.set_isolation_level(level)
        return method(self, *args, **kwargs)
    if not method:
        return lambda method: decorator(_isolationLevel, method)
    return decorator(_isolationLevel, method)
