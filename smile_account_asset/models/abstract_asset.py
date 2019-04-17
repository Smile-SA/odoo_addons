# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class AbstractAsset(models.AbstractModel):
    _name = 'abstract.asset'
    _description = 'Abstract Asset'

    @api.model
    def _get_accounting_methods(self):
        return self.env['account.asset.depreciation.method']. \
            get_methods_selection('accounting')

    @api.model
    def _get_fiscal_methods(self):
        return self.env['account.asset.depreciation.method']. \
            get_methods_selection('fiscal')

    name = fields.Char(required=True)
    # Accounting Method
    accounting_method = fields.Selection(
        _get_accounting_methods, required=True)
    accounting_annuities = fields.Integer()
    accounting_rate = fields.Float(
        'Accounting Amortization Rate (%)', digits=(4, 2))
    accounting_rate_visibility = fields.Boolean(
        'Accounting Amortization Rate Visibility')
    # Fiscal Method
    fiscal_method = fields.Selection(
        _get_fiscal_methods, required=True, default='none')
    fiscal_annuities = fields.Integer()
    fiscal_rate = fields.Float(
        'Fiscal Amortization Rate (%)', digits=(4, 2))
    fiscal_rate_visibility = fields.Boolean(
        'Fiscal Amortization Rate Visibility')

    @api.onchange('accounting_method', 'fiscal_method')
    def _onchange_depreciation_infos(self):
        self.accounting_rate_visibility = False
        self.fiscal_rate_visibility = False
        if self.accounting_method == 'none':
            self.accounting_annuities = 0
            self.fiscal_method = 'none'
        if self.fiscal_method == 'none':
            self.fiscal_annuities = 0
        if self.accounting_method == 'manual' and \
                self.fiscal_method not in ('none', 'manual'):
            self.fiscal_method = 'manual'
        if self.accounting_method:
            method_infos = self.env['account.asset.depreciation.method']. \
                get_method_infos()
            self.accounting_rate_visibility = method_infos[
                self.accounting_method]['use_manual_rate']
            if self.fiscal_method:
                self.fiscal_rate_visibility = method_infos[
                    self.fiscal_method]['use_manual_rate']

    @api.model
    def create(self, vals):
        if not vals.get('fiscal_method'):
            vals.update({
                'fiscal_method': 'none',
                'fiscal_annuities': 0,
                'fiscal_rate': 0,
            })
        return super(AbstractAsset, self).create(vals)

    @api.multi
    def copy_data(self, default=None):
        default = default or {}
        default['name'] = _("%s Copy") % self.name
        return super(AbstractAsset, self).copy_data(default)
