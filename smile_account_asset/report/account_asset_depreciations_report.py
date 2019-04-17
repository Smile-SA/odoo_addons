# -*- coding: utf-8 -*-

from odoo import api, models


class ReportAccountAssetDepreciations(models.AbstractModel):
    _name = 'report.smile_account_asset.report_account_asset_depreciations'
    _inherit = 'account.asset.report.mixin'

    @api.model
    def _get_records(self, data):
        """
        Retourne les immobilisations en service sur la période du rapport
        """
        domain = self._get_records_to_display_domain(data)
        return self.env['account.asset.asset'].search(domain)

    @api.model
    def _get_records_to_display_domain(self, data):
        form = data['form']
        date_from = form['date_from']
        date_to = form['date_to']
        return super(ReportAccountAssetDepreciations, self). \
            _get_records_to_display_domain(data) + [
                ('in_service_account_date', '<=', date_to),
                '|',
                ('state', '!=', 'close'),
                ('sale_account_date', '>=', date_from),
        ]

    @api.model
    def group_by(self, assets, currency, date_to, date_from, is_posted):
        """ Group assets by: account asset.
        Compute asset infos for each asset.
        """
        group_by = {}
        for asset in assets:
            asset_infos = self._get_asset_infos(
                asset, currency, date_to, date_from, is_posted)
            asset_account = asset.asset_account_id
            group_by.setdefault(asset_account, [])
            group_by[asset_account].append((asset, asset_infos))
        return group_by

    @api.model
    def _get_asset_infos(
            self, asset, to_currency, date_to, date_from, is_posted):
        DepreciationLine = self.env['account.asset.depreciation.line']
        from_currency = asset.currency_id
        asset_infos = {
            'purchase': asset.purchase_value_sign,
            'accounting_previous': 0.0,
            'fiscal_previous': 0.0,
            'accounting_period': 0.0,
            'fiscal_period': 0.0,
            'accounting_year': 0.0,
            'fiscal_year': 0.0,
            'accounting_total': 0.0,
            'fiscal_total': 0.0,
        }
        domain = [
            ('asset_id', '=', asset.id),
            ('depreciation_date', '<=', date_to),
            ('depreciation_date', '>=', date_from),
            ('depreciation_type', '!=', 'exceptional'),
        ]
        if is_posted:
            domain += [('is_posted', '=', True)]
        depreciation_lines = DepreciationLine.search(
            domain, order='depreciation_date')
        for index, line in enumerate(depreciation_lines):
            ltype = line.depreciation_type
            if not index:
                asset_infos['%s_previous' % ltype] = \
                    line.previous_years_accumulated_value_sign
            asset_infos['%s_period' % ltype] += \
                line.depreciation_value_sign
            asset_infos['purchase'] = line.purchase_value_sign
            asset_infos['%s_year' % ltype] = \
                line.current_year_accumulated_value_sign
            asset_infos['%s_total' % ltype] = \
                line.current_year_accumulated_value_sign + \
                line.previous_years_accumulated_value_sign
        if not asset.fiscal_depreciation_line_ids:
            for period in ('previous', 'period', 'year', 'total'):
                asset_infos['fiscal_%s' % period] = \
                    asset_infos['accounting_%s' % period]
        else:
            last_fiscal_line = asset.fiscal_depreciation_line_ids.sorted(
                'depreciation_date', reverse=True)[0]
            if last_fiscal_line.depreciation_date.isoformat() < date_from:
                asset_infos['fiscal_previous'] = \
                    asset_infos['fiscal_total'] = last_fiscal_line. \
                    previous_years_accumulated_value_sign
                asset_infos['fiscal_year'] = 0.0
        return self._convert_to_currency(
            asset_infos, from_currency, to_currency)
