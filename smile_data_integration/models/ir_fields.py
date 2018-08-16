# -*- coding: utf-8 -*-
# (C) 2017 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class IrFieldsConverter(models.AbstractModel):
    _inherit = 'ir.fields.converter'

    @api.model
    def _str_to_boolean(self, model, field, value):
        if isinstance(value, bool):
            return value, []
        return super(IrFieldsConverter, self)._str_to_boolean(
            model, field, value)
