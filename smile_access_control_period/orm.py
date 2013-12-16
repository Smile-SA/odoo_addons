# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
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

import time

from openerp import SUPERUSER_ID
from openerp.osv import orm
from openerp.osv.orm import BaseModel
from openerp.tools.translate import _

native_check_access_rights = BaseModel.check_access_rights


def raise_access_exception(self, cr, uid, operation, raise_exception=True, date_from=None, date_to=None):
    if raise_exception:
        msg = _("You can not %s this document (%s)")
        params = [_(operation), self._name]
        if date_from:
            msg += _(" from %s")
            params.append(date_from)
        if date_to:
            msg += _(" to %s")
            params.append(date_to)
        raise orm.except_orm(_('AccessError'), msg % tuple(params))
    return False


def new_check_access_rights(self, cr, uid, operation, raise_exception=True):
    if uid == SUPERUSER_ID:
        return True
    if operation in ('create', 'write', 'unlink'):
        today = time.strftime('%Y-%m-%d')
        date_start, date_stop = self.pool.get('res.users').get_readonly_dates(cr, uid, uid)
        if date_start and date_stop:
            if date_start <= today <= date_stop:
                return self.raise_access_exception(cr, uid, operation, raise_exception, date_start, date_stop)
        elif date_start:  # Only date_start
            if today >= date_start:
                return self.raise_access_exception(cr, uid, operation, raise_exception, date_start)
        elif date_stop:  # Only date_stop
            if today <= date_stop:
                return self.raise_access_exception(cr, uid, operation, raise_exception, date_to=date_stop)
    return native_check_access_rights(self, cr, uid, operation, raise_exception)


BaseModel.check_access_rights = new_check_access_rights
BaseModel.raise_access_exception = raise_access_exception
