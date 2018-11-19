# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import math

from odoo import api, fields, models


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    display_rounding = fields.Float(
        'Display Rounding Factor', digits=(12, 6))
    display_decimal_places = fields.Integer(
        compute='_get_display_decimal_places')

    @api.one
    @api.depends('rounding', 'display_rounding')
    def _get_display_decimal_places(self):
        if not self.display_rounding:
            self.display_decimal_places = self.decimal_places
        elif 0 < self.display_rounding < 1:
            self.display_decimal_places = \
                int(math.ceil(math.log10(1 / self.display_rounding)))
        else:
            self.display_decimal_places = 0
