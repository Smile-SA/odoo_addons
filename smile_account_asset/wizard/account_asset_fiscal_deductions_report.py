# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountAssetFiscalDeductionsReport(models.TransientModel):
    _name = 'fiscal.deductions.report'
    _inherit = 'account.asset.common.report'
    _description = 'Fiscal deductions report'

    category_ids = fields.Many2many(
        domain=[('fiscal_deduction_limit', '!=', 0)])

    def _print_report(self, data):
        return self.env.ref(
            'smile_account_asset.'
            'action_report_fiscal_deductions').report_action(
            self, data=data)
