# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
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

import inspect

from openerp import SUPERUSER_ID
from openerp.osv import orm
from openerp.tools.translate import _


def sartre_validate(self, cr, uid, ids, context=None):
    context = context or {}
    # Added by smile #
    if context.get('no_validate'):
        return
    ##################
    lng = context.get('lang', False) or 'en_US'
    trans = self.pool.get('ir.translation')
    error_msgs = []
    for constraint in self._constraints:
        fun, msg, fields_list = constraint
        args = (self, cr, uid, ids)
        kwargs = {}
        if 'context' in inspect.getargspec(fun)[0]:
            kwargs = {'context': context}
        if not fun(*args, **kwargs):
            if hasattr(msg, '__call__'):
                tmp_msg = msg(self, cr, uid, ids, context=context)
                if isinstance(tmp_msg, tuple):
                    tmp_msg, params = tmp_msg
                    translated_msg = tmp_msg % params
                else:
                    translated_msg = tmp_msg
            else:
                translated_msg = trans._get_source(cr, uid, self._name, 'constraint', lng, msg) or msg
            fields_list = fields_list or []
            if uid == SUPERUSER_ID:
                error_msgs.append(
                    _("Error occurred while validating the field(s) %s: %s") % (','.join(fields_list), translated_msg)
                )
            else:
                error_msgs.append(translated_msg)
            self._invalids.update(fields_list)
    if error_msgs:
        # Added by smile #
        if not context.get('pid_list'):
            cr.rollback()
        ##################
        raise orm.except_orm('ValidateError', '\n'.join(error_msgs))
    else:
        self._invalids.clear()

orm.BaseModel._validate = sartre_validate
