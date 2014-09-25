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

from contextlib import contextmanager

from openerp.modules.registry import RegistryManager
from openerp.tools.func import wraps


@contextmanager
def cursor(cr):
    registry = RegistryManager.get(cr.dbname)
    db = registry._db
    # Pass in transaction isolation level: READ COMMITTED
    new_cr = db.cursor(serialized=False)
    try:
        yield new_cr
        new_cr.commit()
    finally:
        new_cr.close()


def with_new_cursor(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        with cursor(self._cr) as new_cr:
            return method(self.with_env(self.env(cr=new_cr)), *args, **kwargs)
    return wrapper
