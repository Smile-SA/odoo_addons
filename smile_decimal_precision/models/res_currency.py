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
            _logger.debug(
                f"Traitement de la devise ID [{record.id}] {record.name} : "
                f"rounding = {record.rounding}, "
                f"display_rounding = {record.display_rounding}"
            )
            if not record.display_rounding:
                record.display_decimal_places = record.decimal_places
            elif 0 < record.display_rounding < 1:
                record.display_decimal_places = \
                    int(math.ceil(math.log10(1 / record.display_rounding)))
            else:
                record.display_decimal_places = 0
