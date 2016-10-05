# -*- coding: utf-8 -*-

from odoo.api import Environment
from odoo.modules.registry import Registry
from odoo.tools.func import wraps


def cursor(dbname, serialized=True):
    registry = Registry(dbname)
    db = registry._db
    return db.cursor(serialized=serialized)


def with_new_cursor(serialized=True):
    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            with Environment.manage():
                with cursor(self._cr.dbname, serialized=serialized) as new_cr:
                    return method(self.with_env(self.env(cr=new_cr)), *args, **kwargs)
        return wrapper
    return decorator
