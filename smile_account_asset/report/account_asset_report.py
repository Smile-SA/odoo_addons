# -*- coding: utf-8 -*-

from odoo import api, models

from ..tools import get_fiscalyear_start_date


class ReportAccountAssets(models.AbstractModel):
    _name = 'report.smile_account_asset.report_account_assets'
    _inherit = 'account.asset.report.mixin'

    @api.model
    def _get_records(self, data):
        """
        Retourne les immobilisations :
        * acquises définitivement antérieurement à la date de fin
        * non cédée à la date de fin ou cédée depuis le début de l'exercice
            fiscal courant à la date de fin
        """
        domain = self._get_records_to_display_domain(data)
        assets = self.env['account.asset.asset'].search(domain)
        # Nous devons exclure les immos en-cours à une date ultérieure
        # à la date de fin
        histories = self.env['account.asset.history'].search([
            ('asset_id', 'in', assets.ids),
            ('category_id.asset_in_progress', '=', True),
            ('date_to', '>', data['form']['date_to']),
        ])
        return assets - histories.mapped('asset_id')

    @api.model
    def _get_records_to_display_domain(self, data):
        form = data['form']
        date_to = form['date_to']
        fiscalyear_start_day = self.env.user.company_id.fiscalyear_start_day
        fiscalyear_start_date = \
            get_fiscalyear_start_date(date_to, fiscalyear_start_day)
        return super(ReportAccountAssets, self). \
            _get_records_to_display_domain(data) + [
                ('state', '!=', 'draft'),
                ('category_id.asset_in_progress', '=', False),
                '|',
                ('purchase_account_date', '<=', date_to),
                '&',
                ('purchase_account_date', '=', False),
                ('purchase_date', '<=', date_to),
                '|',
                ('purchase_cancel_move_id', '=', False),
                ('purchase_cancel_move_id.date', '>', date_to),
                '|',
                ('state', '!=', 'close'),
                ('sale_account_date', '>=', fiscalyear_start_date),
        ]

    @api.model
    def group_by(self, assets, currency, date_to, is_posted):
        """ Group assets by: account asset.
        Compute asset infos for each asset.
        """
        group_by = {}
        for asset in assets:
            asset_infos = self._get_asset_infos(
                asset, currency, date_to, is_posted)
            asset_account = asset.asset_account_id
            group_by.setdefault(asset_account, [])
            group_by[asset_account].append((asset, asset_infos))
        return group_by

    @api.model
    def _get_asset_infos(self, asset, to_currency, date_to, is_posted):
        from_currency = asset.currency_id
        depreciation_line = asset._get_last_depreciation(date_to, is_posted)
        if depreciation_line:
            res = {
                'purchase': depreciation_line.purchase_value_sign,
                'salvage': depreciation_line.salvage_value_sign,
                'previous': depreciation_line.
                previous_years_accumulated_value_sign,
                'current': depreciation_line.
                current_year_accumulated_value_sign,
                'book': depreciation_line.book_value_sign,
            }
        else:
            for history in asset.asset_history_ids.sorted('date_to'):
                if history.date_to.isoformat() > date_to:
                    res = {
                        'purchase': history.purchase_value_sign,
                        'salvage': history.salvage_value_sign,
                        'previous': 0.0,
                        'current': 0.0,
                        'book': history.purchase_value_sign,
                    }
                    break
            else:
                res = {
                    'purchase': asset.purchase_value_sign,
                    'salvage': asset.salvage_value_sign,
                    'previous': 0.0,
                    'current': 0.0,
                    'book': asset.purchase_value_sign,
                }
        res['next'] = res['previous'] + res['current']
        return self._convert_to_currency(res, from_currency, to_currency)
