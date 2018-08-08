# -*- coding: utf-8 -*-

from odoo import api
from odoo.models import BaseModel

from ..tools import with_new_cursor


@api.multi
@with_new_cursor(False)
def write_with_new_cursor(self, vals):
    return self.write(vals)


BaseModel.write_with_new_cursor = write_with_new_cursor
