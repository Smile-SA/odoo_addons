# -*- coding: utf-8 -*-

from odoo import api, fields, models

from ..tools import get_fiscalyear_start_date


class ReportFiscalDeductions(models.AbstractModel):
    _name = 'report.smile_account_asset.report_fiscal_deductions'
    _inherit = 'account.asset.report.mixin'

    @api.model
    def _get_records(self, data):
        """
        Retourne les immobilisations bénéficiant d'une déduction fiscale
        en service à la date de fin ou cédée dans l'exercice de la date de fin
        """
        domain = self._get_records_to_display_domain(data)
        return self.env['account.asset.asset'].search(domain)

    @api.model
    def _get_records_to_display_domain(self, data):
        form = data['form']
        date_to = form['date_to']
        fiscalyear_start_day = self.env.user.company_id.fiscalyear_start_day
        fiscalyear_start_date = \
            get_fiscalyear_start_date(date_to, fiscalyear_start_day)
        return super(ReportFiscalDeductions, self). \
            _get_records_to_display_domain(data) + [
                ('state', 'not in', ('draft', 'confirm')),
                ('parent_id', '=', False),
                ('category_id.fiscal_deduction_limit', '!=', False),
                '|',
                ('in_service_account_date', '<=', date_to),
                '&',
                ('in_service_account_date', '=', False),
                ('in_service_date', '<=', date_to),
                '|',
                ('purchase_cancel_move_id', '=', False),
                ('purchase_cancel_move_id.date', '>', date_to),
                '|',
                ('state', '!=', 'close'),
                ('sale_account_date', '>=', fiscalyear_start_date),
        ]

    @api.model
    def group_by(self, assets, currency, date_to):
        """ Group assets by: account asset.
        Compute asset infos for each asset.
        """
        group_by = {}
        for asset in assets:
            asset_infos = self._get_asset_infos(asset, currency, date_to)
            asset_account = asset.asset_account_id
            group_by.setdefault(asset_account, [])
            group_by[asset_account].append((asset, asset_infos))
        return group_by

    @api.model
    def _get_asset_infos(self, asset, to_currency, date_to):
        from_currency = asset.currency_id
        date_to_year = fields.Date.from_string(date_to).year
        purchase = current = accumulated = 0.0
        for asset_ in asset.child_ids | asset:
            purchase += asset_.purchase_value_sign or 0.0
            depreciation_lines = asset_.accounting_depreciation_line_ids. \
                filtered(lambda line: line.is_posted and line.active and
                         line.depreciation_date <= fields.Date.from_string(
                             date_to)).sorted('depreciation_date')
            if depreciation_lines:
                last_depreciation_line = depreciation_lines[-1]
                accumulated += last_depreciation_line. \
                    previous_years_accumulated_value_sign + \
                    last_depreciation_line.current_year_accumulated_value_sign
                if last_depreciation_line.year == date_to_year:
                    current += last_depreciation_line. \
                        current_year_accumulated_value_sign
        book = purchase - accumulated
        nd_rate = 0.0
        if purchase > 0:
            nd_rate = (purchase - min(
                purchase, asset.category_id.fiscal_deduction_limit)
            ) / purchase
            current_nd = current * nd_rate
            accumulated_nd = accumulated * nd_rate
        in_service_account_date_year = fields.Date.from_string(
            asset.in_service_account_date or asset.in_service_date).year
        if in_service_account_date_year == date_to_year:
            depreciation_lines = asset.accounting_depreciation_line_ids. \
                filtered(lambda line: line.is_posted and line.active and
                         line.depreciation_date <= fields.Date.from_string(
                             date_to)).sorted('depreciation_date')
            if depreciation_lines:
                first_line_year = fields.Date.from_string(
                    depreciation_lines[0].depreciation_date).year
                if first_line_year == in_service_account_date_year - 1:
                    current_nd = accumulated_nd = accumulated
                    current = accumulated = 0.0
        res = {
            'purchase_date': asset.purchase_date,
            'sale_date': asset.sale_date if asset.state == 'close' else '',
            'purchase': purchase,
            'current': current,
            'current_nd': current_nd,
            'accumulated': accumulated,
            'accumulated_nd': accumulated_nd,
            'book': book,
        }
        return self._convert_to_currency(res, from_currency, to_currency)
