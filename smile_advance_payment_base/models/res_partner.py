# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_account_payable_advance_id = fields.Many2one(
        'account.account', "Account Advance Payable",
        domain=[
            ('internal_type', '=', 'other'),
            ('deprecated', '=', False),
        ], company_dependent=True)
    property_account_receivable_advance_id = fields.Many2one(
        'account.account', "Account Advance Receivable",
        domain=[
            ('internal_type', '=', 'other'),
            ('deprecated', '=', False),
        ], company_dependent=True)
