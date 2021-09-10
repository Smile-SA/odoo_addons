# -*- coding: utf-8 -*-
# (C) 2019 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResourceResource(models.Model):
    _inherit = 'resource.resource'

    name = fields.Char(
        data_mask="'resource_' || id::text WHERE resource_type = 'user'")
    code = fields.Char(data_mask="NULL")
