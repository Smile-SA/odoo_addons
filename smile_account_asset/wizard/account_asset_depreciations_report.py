# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountAssetDepreciationsReport(models.TransientModel):
    _name = 'account.asset.depreciations.report'
    _inherit = 'account.asset.common.report'
    _description = 'Asset depreciations report'

    only_total = fields.Boolean('Only total', default=True)

    def _print_report(self, data):
        return self.env.ref(
            'smile_account_asset.'
            'action_report_account_asset_depreciations').report_action(
            self, data=data)
