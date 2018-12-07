# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class PagerLimit(models.AbstractModel):
    _name = 'ir.pager_limit'
    _description = 'Pager limit'

    @api.model
    def get_value(self):
        return int(self.env['ir.config_parameter'].sudo().get_param(
            'pager.limit', 1000))
