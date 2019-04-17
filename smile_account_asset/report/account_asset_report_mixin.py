# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError


class AccountAssetReportMixin(models.AbstractModel):
    _name = 'account.asset.report.mixin'

    @api.model
    def _get_report_values(self, docids, data=None):
        if data is None or not data.get('form'):
            raise UserError(
                _("Form content is missing, this report cannot be printed."))
        records = self._get_records(data)
        return {
            'doc_ids': records.ids,
            'doc_model': records and records[0]._name,
            'data': data,
            'docs': records,
            'group_by': self.group_by,
        }

    @api.model
    def _get_records(self, data):
        raise NotImplementedError(
            "Method _get_records() undefined on {}".format(self))

    @api.model
    def _get_records_to_display_domain(self, data):
        domain = []
        form = data['form']
        if form['category_ids']:
            domain += [('category_id', 'in', form['category_ids'])]
        if form['partner_ids']:
            domain += [('supplier_id', 'in', form['partner_ids'])]
        if form['account_ids']:
            domain += [('asset_account_id', 'in', form['account_ids'])]
        return domain

    @api.model
    def group_by(self, records):
        raise NotImplementedError(
            "Method group_by() undefined on {}".format(self))

    @api.model
    def _convert_to_currency(self, res, from_currency, to_currency):
        # INFO: please use this method carefully.
        # It converts amounts inside dict to the currency given in argument.
        if from_currency != to_currency:
            for key, value in res.items():
                if isinstance(value, (int, float)):
                    res[key] = from_currency.compute(value, to_currency)
        return res
