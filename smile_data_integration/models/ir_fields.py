# -*- coding: utf-8 -*-

from odoo import api, models


class IrFieldsConverter(models.AbstractModel):
    _inherit = 'ir.fields.converter'

    @api.model
    def _str_to_boolean(self, model, field, value):
        if isinstance(value, bool):
            return value, []
        return super(IrFieldsConverter, self)._str_to_boolean(
            model, field, value)
