# -*- coding: utf-8 -*-

from odoo import models


class AccountAssetsInProgress(models.TransientModel):
    _name = 'account.assets.in.progress.report'
    _inherit = 'account.asset.common.report'
    _description = 'Assets in progress report'

    def _print_report(self, data):
        return self.env.ref(
            'smile_account_asset.'
            'action_report_account_assets_in_progress').report_action(
            self, data=data)
