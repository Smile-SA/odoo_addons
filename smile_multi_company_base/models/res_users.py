# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    company_id = fields.Many2one(domain=[('allows_to_log_in', '=', True)])
    company_ids = fields.Many2many(domain=[('allows_to_log_in', '=', True)])
