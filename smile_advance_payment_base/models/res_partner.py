# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_account_payable_advance_id = fields.Many2one(
        'account.account', "Account Advance Payable",
        domain=[
            ('internal_type', '=', 'payable'),
            ('deprecated', '=', False),
        ], company_dependent=True)
    property_account_receivable_advance_id = fields.Many2one(
        'account.account', "Account Advance Receivable",
        domain=[
            ('internal_type', '=', 'receivable'),
            ('deprecated', '=', False),
        ], company_dependent=True)
