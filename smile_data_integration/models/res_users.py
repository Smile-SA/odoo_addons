# -*- coding: utf-8 -*-
# (C) 2020 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, tools


class ResUsers(models.Model):
    _inherit = 'res.users'

    context_active_test = fields.Boolean(default=True)
    context_raise_load_exceptions = fields.Boolean()
    context_data_integration = fields.Boolean()

    @api.model
    @tools.ormcache('self._uid')
    def context_get(self):
        return dict(super(ResUsers, self).context_get())
