# -*- coding: utf-8 -*-

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    context_active_test = fields.Boolean()
    context_raise_load_exceptions = fields.Boolean()
