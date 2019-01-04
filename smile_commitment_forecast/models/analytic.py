# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class AnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    forecast = fields.Boolean()
