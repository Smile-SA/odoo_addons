# -*- coding: utf-8 -*-
# (C) 2010 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class EnvRibbon(models.AbstractModel):
    _name = 'ir.env_ribbon'
    _description = 'Environment Ribbon'

    @api.model
    def get_values(self):
        Param = self.env['ir.config_parameter'].sudo()
        label = Param.get_param('server.environment') or 'prod'
        color = Param.get_param('server.environment.ribbon_color') or \
            'rgba(255, 0, 0, .6)'
        return label, color
