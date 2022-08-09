# -*- coding: utf-8 -*-
# (C) 2022 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ApiRestTag(models.Model):
    _name = 'api.rest.tag'
    _description = "Api Rest Tag"

    name = fields.Char(required=True)
    description = fields.Char()
