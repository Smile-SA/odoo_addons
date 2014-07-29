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

import logging

from openerp.models import BaseModel

_logger = logging.getLogger(__package__)

native_store_set_values = BaseModel._store_set_values


def new_store_set_values(self, cr, uid, ids, fields, context):
    context = context or {}
    if not context.get('store_in_secure_mode'):
        return native_store_set_values(self, cr, uid, ids, fields, context)
    res_ids_in_error = {}
    for res_id in ids:
        try:
            native_store_set_values(self, cr, uid, [res_id], fields, context)
        except Exception, e:
            res_ids_in_error[res_id] = e
            continue
    model = self.__class__.__name__
    if res_ids_in_error:
        _logger.error('%s._store_set_values FAILED: %s', model, repr(res_ids_in_error))
    else:
        _logger.debug('%s._store_set_values SUCCESS', model)
    return True

BaseModel._store_set_values = new_store_set_values
