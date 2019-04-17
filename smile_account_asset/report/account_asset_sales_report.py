# -*- coding: utf-8 -*-

from odoo import api, models


class ReportAccountAssetSales(models.AbstractModel):
    _name = 'report.smile_account_asset.report_account_asset_sales'
    _inherit = 'account.asset.report.mixin'

    @api.model
    def _get_records(self, data):
        """
        Retourne les immobilisations cédées au cours de la période
        """
        domain = self._get_records_to_display_domain(data)
        assets = self.env['account.asset.asset'].search(domain)
        # Supprime les immobilisations dont la cession a été annulée
        # entre la date de dernière cession et la date de fin
        for asset in assets[:]:
            if asset.sale_cancel_move_id and \
                    asset.sale_move_id.id < asset.sale_cancel_move_id.id and \
                    asset.sale_cancel_move_id.date <= data['form']['date_to']:
                assets -= asset
        return assets

    @api.model
    def _get_records_to_display_domain(self, data):
        form = data['form']
        date_from = form['date_from']
        date_to = form['date_to']
        # Ne disposant pas des dates successives de cession et d'annulation
        # de cession, je suis incapable de savoir si l'immo a été cédée
        # au cours de la période sans que sa cession ait été annulée
        # avant la fin de la période
        return super(ReportAccountAssetSales, self). \
            _get_records_to_display_domain(data) + [
                ('sale_account_date', '>=', date_from),
                ('sale_account_date', '<=', date_to),
        ]

    @api.model
    def group_by(self, assets, currency):
        """ Group assets by: account asset.
        Compute asset infos for each asset.
        Compute global tax for all assets.
        """
        group_by = {}
        global_result = {
            'sale_result': 0.0,
            'tax_add': 0.0,
            'tax_origin': 0.0,
            'tax_to_pay': 0.0,
        }
        for asset in assets:
            asset_infos = self._get_asset_infos(asset, currency)
            asset_account = asset.asset_account_id
            group_by.setdefault(asset_account, [])
            group_by[asset_account].append((asset, asset_infos))
            # Compute global tax amounts
            self._update_global_result(
                global_result, asset, asset_infos, currency)
        return (group_by, global_result)

    @api.model
    def _get_asset_infos(self, asset, to_currency):
        from_currency = asset.currency_id
        sign = self._get_asset_sign(asset)
        res = {
            'purchase': asset.purchase_value * sign,
            'book': asset.fiscal_book_value * sign,
            'amortization': asset.accumulated_amortization_value * sign,
            'sale': asset.sale_value * sign,
            'sale_result': (asset.sale_value - asset.book_value) * sign,
        }
        return self._convert_to_currency(res, from_currency, to_currency)

    @api.model
    def _get_asset_sign(self, asset):
        return asset.asset_type == 'purchase_refund' and -1 or 1

    @api.model
    def _update_global_result(
            self, global_result, asset, asset_infos, to_currency):
        from_currency = asset.currency_id
        sign = self._get_asset_sign(asset)
        global_result['sale_result'] += asset_infos['sale_result']
        global_result['tax_origin'] += from_currency.compute(
            asset.purchase_tax_amount * sign, to_currency)
        regularization_tax_amount = from_currency.compute(
            asset.regularization_tax_amount, to_currency)
        if regularization_tax_amount >= 0.0:
            global_result['tax_to_pay'] += \
                abs(regularization_tax_amount) * sign
        else:
            global_result['tax_add'] += abs(regularization_tax_amount) * sign
