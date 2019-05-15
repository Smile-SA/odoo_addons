# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountAssetsInProgress(models.TransientModel):
    _name = 'account.assets.in.progress.report'
    _inherit = 'account.asset.common.report'
    _description = 'Assets in progress report'

    date_from = fields.Date(required=False)

    @api.model
    def _get_default_date_from(self):
        return False

    @api.onchange('date_to', 'company_id')
    def _onchange_date_to(self):
        if self.date_from:
            return super(AccountAssetsInProgress, self)._onchange_date_to()

    def _print_report(self, data):
        return self.env.ref(
            'smile_account_asset.'
            'action_report_account_assets_in_progress').report_action(
            self, data=data)
