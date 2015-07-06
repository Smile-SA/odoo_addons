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

from datetime import datetime
from dateutil.relativedelta import relativedelta
import re

from openerp.models import BaseModel
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

RELATIVEDELTA_TYPES = {
    'Y': 'years',
    'm': 'months',
    'W': 'weeks',
    'd': 'days',
    'H': 'hours',
    'M': 'minutes',
}

native_where_calc = BaseModel._where_calc


def _where_calc(self, cr, uid, domain, active_test=True, context=None):
    match_pattern = re.compile('^[+-]{0,1}[0-9]*[YmdHM]$')
    group_pattern = re.compile(r'(?P<value>^[+-]{0,1}[0-9]*)(?P<type>[YmWdHM]$)')
    for cond in domain or []:
        if isinstance(cond, (tuple, list)) and isinstance(cond[2], basestring) and match_pattern.match(cond[2]):
            value_format = None
            model = self._name
            for fieldname in cond[0].split('.'):
                field = self.pool[model]._fields[fieldname]
                model = field.comodel_name
                if not model and field.type in ('datetime', 'date'):
                    value_format = field.type == 'date' and DEFAULT_SERVER_DATE_FORMAT or DEFAULT_SERVER_DATETIME_FORMAT
            if value_format:
                vals = group_pattern.match(cond[2]).groupdict()
                args = {RELATIVEDELTA_TYPES[vals['type']]: int(vals['value'])}
                cond[2] = (datetime.now() - relativedelta(**args)).strftime(value_format)
    return native_where_calc(self, cr, uid, domain, active_test, context)

BaseModel._where_calc = _where_calc
