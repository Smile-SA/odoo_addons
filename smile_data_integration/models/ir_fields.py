# -*- coding: utf-8 -*-
# (C) 2020 Smile (<https://www.smile.eu>)
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

    @api.model
    def db_id_for(self, model, field, subfield, value):
        self = self.with_context(active_test=False)
        return super(IrFieldsConverter, self).db_id_for(
            model, field, subfield, value)
