# -*- coding: utf-8 -*-
# (C) 2026 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from contextlib import ExitStack
from functools import wraps

from odoo.modules.registry import Registry


def with_impex_cursor(autocommit=True):
    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            with ExitStack() as stack, \
                    Registry(self.env.cr.dbname).cursor() as new_cr:
                # autocommit: each insert/update request
                # will be performed atomically.
                # Thus everyone (with another cursor)
                # can access to a running impex record
                new_cr._cnx.autocommit = autocommit
                # impex_stack: cursors kept open (e.g. row locks)
                # until the end of the decorated method
                self = self.with_env(self.env(cr=new_cr)).with_context(
                    original_cr=self.env.cr, impex_stack=stack,
                )
                return method(self, *args, **kwargs)

        return wrapper

    return decorator
