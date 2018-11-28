# -*- coding: utf-8 -*-
# (C) 2010 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, tools


class EnvRibbon(models.AbstractModel):
    _name = 'ir.env_ribbon'
    _description = 'Environment Ribbon'

    @api.model
    def get_values(self):
        label = tools.config.get('server.environment') or 'prod'
        label = label.upper()
        if tools.config.get('server.environment.display_dbname_in_ribbon'):
            label += "<br/>(%s)" % self._cr.dbname
        color = tools.config.get('server.environment.ribbon_color') or \
            'rgba(255, 0, 0, .6)'
        return label, color
