# (C) 2025 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class IrQwebFieldFloat(models.AbstractModel):
    _inherit = 'ir.qweb.field.float'

    @api.model
    def record_to_html(self, record, field_name, options):
        if 'precision' not in options and 'decimal_precision' not in options:
            digits = record._fields[field_name].get_description(
                record.env, ['digits']).get('digits')
            if digits:
                options = dict(options, precision=digits[1])
        return super().record_to_html(record, field_name, options)
