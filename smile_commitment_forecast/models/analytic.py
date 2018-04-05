# -*- coding: utf-8 -*-

from odoo import fields, models


class AnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    forecast = fields.Boolean()
