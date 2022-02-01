# -*- coding: utf-8 -*-
# (C) 2022 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import secrets

from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    api_rest_key = fields.Char()

    def generate_api_rest_key(self):
        self.ensure_one()
        if self.api_rest_key:
            return
        while True:
            api_rest_key = secrets.token_urlsafe(40)
            if not self.sudo().search([('api_rest_key', '=', api_rest_key)]):
                self.sudo().write({'api_rest_key': api_rest_key})
                return

    @api.model
    def get_api_rest_user(self, api_rest_key):
        return self.sudo().search([
            ('api_rest_key', '=', api_rest_key)
        ], limit=1)
