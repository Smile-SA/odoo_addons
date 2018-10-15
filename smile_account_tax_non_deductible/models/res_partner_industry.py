# -*- coding: utf-8 -*-
# (C) 2013 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartnerIndustry(models.Model):
    _inherit = 'res.partner.industry'
    _order = 'sequence asc, name asc'

    name = fields.Char(required=True)
    full_name = fields.Char('Code', required=True)
    company_id = fields.Many2one('res.company', 'Company')
    sequence = fields.Integer(default=15)
    taxation_rate_ids = fields.One2many(
        'account.tax.rate', 'industry_id', 'Taxation rates',
        domain=[('rate_type', '=', 'taxation')],
        context={'default_rate_type': 'taxation'})

    _sql_constraints = [
        ('uniq_name', 'unique(name)', 'Industry name must be unique'),
    ]

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = [
            '|',
            ('name', operator, name),
            ('full_name', operator, name),
        ] + (args or [])
        return super(ResPartnerIndustry, self).name_search(
            name, args, operator, limit)
