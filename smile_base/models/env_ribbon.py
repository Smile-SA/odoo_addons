# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, models, tools


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
