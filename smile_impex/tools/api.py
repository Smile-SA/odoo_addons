# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import registry
from odoo.tools.func import wraps


def with_impex_cursor(autocommit=True):
    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            with registry(self._cr.dbname).cursor() as new_cr:
                # autocommit: each insert/update request
                # will be performed atomically.
                # Thus everyone (with another cursor)
                # can access to a running impex record
                new_cr._cnx.autocommit = True
                self = self.with_env(self.env(cr=new_cr)).with_context(
                    original_cr=self._cr
                )
                return method(self, *args, **kwargs)

        return wrapper

    return decorator
