# (C) 2025 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import math

from odoo import api, fields, models


import logging
_logger = logging.getLogger(__name__)


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    display_rounding = fields.Float('Display Rounding Factor', digits=(12, 6))
    display_decimal_places = fields.Integer(
        compute='_get_display_decimal_places')

    @api.depends('rounding', 'display_rounding')
    def _get_display_decimal_places(self):
        for record in self:
            _logger.debug(f"Traitement de la devise ID"
                          f" [{record.id}] {record.name} : "
                          f"rounding = {record.rounding},"
                          f" display_rounding = {record.display_rounding}")
            if not record.display_rounding:
                record.display_decimal_places = record.decimal_places
            elif 0 < record.display_rounding < 1:
                record.display_decimal_places = \
                    int(math.ceil(math.log10(1 / record.display_rounding)))
            else:
                record.display_decimal_places = 0

    @api.model
    def get_all_currencies(self):
        res = super().get_all_currencies()
        display = {c.id: c.display_decimal_places
                   for c in self.sudo().browse(list(res))}
        return {
            cid: dict(vals, digits=[vals['digits'][0], display[cid]])
            for cid, vals in res.items()
        }
