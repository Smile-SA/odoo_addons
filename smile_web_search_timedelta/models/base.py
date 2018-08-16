# -*- coding: utf-8 -*-
# (C) 2015 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime
from dateutil.relativedelta import relativedelta
import re
from six import string_types

from odoo import api, models
from odoo.tools import \
    DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

RELATIVEDELTA_TYPES = {
    'Y': 'years',
    'm': 'months',
    'W': 'weeks',
    'd': 'days',
    'H': 'hours',
    'M': 'minutes',
}


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def _where_calc(self, domain, active_test=True):
        match_pattern = re.compile('^[+-]{0,1}[0-9]*[YmdHM]$')
        group_pattern = re.compile(
            r'(?P<value>^[+-]{0,1}[0-9]*)(?P<type>[%s]$)'
            % ''.join(RELATIVEDELTA_TYPES.keys()))
        for cond in domain or []:
            if isinstance(cond, (tuple, list)) and \
                    isinstance(cond[2], string_types) and \
                    match_pattern.match(cond[2]):
                value_format = None
                model = self._name
                for fieldname in cond[0].split('.'):
                    field = self.env[model]._fields[fieldname]
                    model = field.comodel_name
                    if not model and field.type in ('datetime', 'date'):
                        value_format = field.type == 'date' and \
                            DEFAULT_SERVER_DATE_FORMAT or \
                            DEFAULT_SERVER_DATETIME_FORMAT
                if value_format:
                    vals = group_pattern.match(cond[2]).groupdict()
                    args = {
                        RELATIVEDELTA_TYPES[vals['type']]: int(vals['value']),
                    }
                    cond[2] = (datetime.now() - relativedelta(**args)). \
                        strftime(value_format)
        return super(Base, self)._where_calc(domain, active_test)
