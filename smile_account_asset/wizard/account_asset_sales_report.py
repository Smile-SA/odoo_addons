# -*- coding: utf-8 -*-

from odoo import models


class AccountAssetsSales(models.TransientModel):
    _name = 'account.asset.sales.report'
    _inherit = 'account.asset.common.report'
    _description = 'Account asset sales report'

    def _print_report(self, data):
        return self.env.ref(
            'smile_account_asset.'
            'action_report_account_asset_sales').report_action(
            self, data=data)
