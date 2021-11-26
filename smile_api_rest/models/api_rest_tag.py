# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class ApiRestTag(models.Model):
    _name = 'api.rest.tag'

    name = fields.Char(required=True)
    description = fields.Char()
