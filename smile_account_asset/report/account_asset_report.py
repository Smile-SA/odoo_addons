# -*- coding: utf-8 -*-

from odoo import api, fields, models

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
            # We only have to adjust amounts in this case, because
            # when we read values inside asset history, previous value
            # is already set to 0
            self._adjust_previous_amounts(res, asset, date_to, is_posted)
        else:
            for history in asset.asset_history_ids.sorted('date_to'):
                if history.date_to > date_to:
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

    def _adjust_previous_amounts(self, asset_infos, asset, date_to, is_posted):
        """
        Ensure that depreciation lines having depreciation date on
        a previous year but that related to an asset having Entry
        into service date on the current year are displayed
        with a null amount on the previous year.
        """
        DepreciationLine = self.env['account.asset.depreciation.line']
        domain = [
            ('asset_id', '=', asset.id),
            ('depreciation_date', '<=', date_to),
        ]
        if is_posted:
            domain += [('is_posted', '=', True)]
        depreciation_lines = DepreciationLine.search(
            domain, order='depreciation_date asc')
        if not depreciation_lines:
            return
        in_service_account_date_year = fields.Date.from_string(
            asset.in_service_account_date).year
        first_line_year = fields.Date.from_string(
            depreciation_lines[0].depreciation_date).year
        date_to_year = fields.Date.from_string(date_to).year
        if first_line_year == date_to_year - 1 and \
                in_service_account_date_year == date_to_year:
            current = asset_infos['previous'] + asset_infos['current']
            asset_infos.update({
                'previous': 0.0,
                'current': current,
            })
