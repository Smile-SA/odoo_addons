# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    context_active_test = fields.Boolean(default=True)
    context_raise_load_exceptions = fields.Boolean()
    context_data_integration = fields.Boolean()
