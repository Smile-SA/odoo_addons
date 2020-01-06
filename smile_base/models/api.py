# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api

_logger = logging.getLogger(__name__)

native_add_todo = api.Environment.add_to_compute


def add_to_compute(self, field, records):
    if not self.registry:
        _logger.warning('%s not recomputed (%s)' % (field, field.related))
        return
    return native_add_todo(self, field, records)


api.Environment.add_to_compute = add_to_compute
