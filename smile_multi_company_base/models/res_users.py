# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    company_id = fields.Many2one(domain=[('allows_to_log_in', '=', True)])
    company_ids = fields.Many2many(domain=[('allows_to_log_in', '=', True)])
