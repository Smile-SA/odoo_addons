# -*- coding: utf-8 -*-
# (C) 2019 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    name = fields.Char(data_mask="'calendar_' || id::text")
