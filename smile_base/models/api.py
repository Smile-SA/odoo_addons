# -*- coding: utf-8 -*-
# (C) 2010 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api

_logger = logging.getLogger(__name__)

native_add_todo = api.Environment.add_todo


def add_todo(self, field, records):
    if not self.registry.field_sequence(field):
        _logger.warning('%s not recomputed (%s)' % (field, field.related))
        return
    return native_add_todo(self, field, records)


api.Environment.add_todo = add_todo
