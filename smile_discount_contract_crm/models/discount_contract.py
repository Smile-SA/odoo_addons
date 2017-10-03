# -*- coding: utf-8 -*-

from odoo import fields, models


class DiscountContract(models.Model):
    _inherit = 'discount.contract'

    opportunity_id = fields.Many2one('crm.lead', 'Opportunity',
                                     domain="[('type', '=', 'opportunity')]")
