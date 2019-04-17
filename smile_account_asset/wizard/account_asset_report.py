# -*- coding: utf-8 -*-

from odoo import models


class AccountAssetReport(models.TransientModel):
    _name = 'account.asset.report'
    _inherit = 'account.asset.common.report'
    _description = 'Assets Report'

    def _print_report(self, data):
        return self.env.ref(
            'smile_account_asset.action_report_account_assets').report_action(
            self, data=data)
