# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class CodeVersion(models.AbstractModel):
    _name = 'ir.code_version'
    _description = 'Code Version'

    @api.model
    def get_value(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'code.version') or '?!'
