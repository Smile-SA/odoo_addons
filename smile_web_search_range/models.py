# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>).
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

from openerp.models import BaseModel

native_where_calc = BaseModel._where_calc


def _where_calc(self, cr, uid, domain, active_test=True, context=None):
    new_domain = []
    for cond in domain or []:
        if isinstance(cond, (tuple, list)) and cond[1] == '><':
            field = cond[0]
            values = cond[2]
            assert isinstance(values, (tuple, list)) and len(values) == 2, "The third item must be a couple if the operator is equals to '><'"
            new_domain.extend(['&', (field, '>=', values[0]), (field, '<=', values[1])])
        else:
            new_domain.append(cond)
    return native_where_calc(self, cr, uid, new_domain, active_test, context)

BaseModel._where_calc = _where_calc
