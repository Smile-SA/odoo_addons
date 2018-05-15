# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    industry_ids = fields.One2many(
        'res.partner.industry', 'company_id', 'Industries')
