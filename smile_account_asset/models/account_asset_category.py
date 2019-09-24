# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.osv import expression

ASSET_CLASSES = [
    ('tangible', 'Tangible'),
    ('intangible', 'Intangible'),
]


class AccountAssetCategory(models.Model):
    _name = 'account.asset.category'
    _description = 'Asset Category'
    _inherit = ['abstract.asset', 'mail.thread']

    @api.model
    def _get_default_company(self):
        return self.env['res.company']._company_default_get(self._name)

    name = fields.Char(translate=True)
    code = fields.Char(required=True)
    active = fields.Boolean(default=True)
    asset_class = fields.Selection(ASSET_CLASSES, required=True)
    asset_in_progress = fields.Boolean()
    company_id = fields.Many2one(
        'res.company', 'Company', required=True, ondelete='restrict',
        default=_get_default_company, index=True,
        help="You cannot change company once an asset was posted.")
    currency_id = fields.Many2one(
        related='company_id.currency_id', ondelete='restrict', readonly=True)
    asset_creation = fields.Selection([
        ('auto', 'Automatic'),
        ('manual', 'Manual'),
    ], "Asset Creation", required=True, default='auto',
        help="If automatic, an asset is created at invoice validation "
             "for each line associated to this asset category")
    confirm_asset = fields.Boolean(
        "Skip Draft State", help="Only in automatic mode")
    asset_ids = fields.One2many(
        'account.asset.asset', 'category_id', 'Assets',
        readonly=True, copy=False)
    invoice_line_ids = fields.One2many(
        'account.invoice.line', 'asset_category_id',
        'Invoice Lines', readonly=True, copy=False)
    accounting_rate = fields.Float(default=25.0)
    fiscal_rate = fields.Float(default=25.0)
    # Asset Purchase
    asset_journal_id = fields.Many2one(
        'account.journal', 'Asset Journal', required=True, ondelete='restrict')
    asset_account_id = fields.Many2one(
        'account.account', 'Asset Account', required=True, ondelete='restrict',
        domain=[('deprecated', '=', False)])
    asset_analytic_account_id = fields.Many2one(
        'account.analytic.account', 'Analytic Account', ondelete='restrict')
    # Asset Amortization
    depreciation_journal_id = fields.Many2one(
        'account.journal', 'Amortization Journal', ondelete='restrict',
        help="Keep empty to use a unique journal for assets and amortizations")
    accounting_depreciation_account_id = fields.Many2one(
        'account.account', 'Amortization Account', ondelete='restrict',
        domain=[('deprecated', '=', False)])
    accounting_depreciation_expense_account_id = fields.Many2one(
        'account.account', 'Amortization Expense Account', ondelete='restrict',
        domain=[('deprecated', '=', False)])
    accounting_depreciation_income_account_id = fields.Many2one(
        'account.account', 'Amortization Income Account', ondelete='restrict',
        domain=[('deprecated', '=', False)])
    # Asset Depreciation
    exceptional_depreciation_account_id = fields.Many2one(
        'account.account', 'Depreciation Account', ondelete='restrict',
        domain=[('deprecated', '=', False)])
    exceptional_depreciation_expense_account_id = fields.Many2one(
        'account.account', 'Depreciation Expense Account', ondelete='restrict',
        domain=[('deprecated', '=', False)])
    exceptional_depreciation_income_account_id = fields.Many2one(
        'account.account', 'Depreciation Income Account', ondelete='restrict',
        domain=[('deprecated', '=', False)])
    # Asset Sale
    sale_journal_id = fields.Many2one(
        'account.journal', 'Disposal Journal', ondelete='restrict',
        help="Keep empty to use a unique journal "
             "for asset acquisition and disposal")
    sale_receivable_account_id = fields.Many2one(
        'account.account', 'Disposal Receivable Account',
        required=True, ondelete='restrict',
        domain=[('deprecated', '=', False)])
    sale_expense_account_id = fields.Many2one(
        'account.account', 'Disposal Expense Account',
        required=True, ondelete='restrict',
        domain=[('deprecated', '=', False)])
    sale_income_account_id = fields.Many2one(
        'account.account', 'Disposal Income Account',
        required=True, ondelete='restrict',
        domain=[('deprecated', '=', False)])
    sale_analytic_account_id = fields.Many2one(
        'account.analytic.account', 'Disposal Analytic Account',
        ondelete='restrict')
    # Fisc
    fiscal_deduction_limit = fields.Monetary('Fiscal Deduction Limit')
    tax_regularization_period = fields.Integer(
        'Tax Regularization Period', help="In years")
    tax_regularization_base = fields.Selection([
        ('deducted', 'Deducted'),
        ('undeducted', 'Undeducted'),
    ], 'Tax Regularization Base', required=True, default='deducted')
    tax_regularization_application = fields.Selection([
        ('with_sale_taxes', 'Taxed Sale'),
        ('without_sale_taxes', 'Untaxed Sale'),
    ], 'Tax Regularization Application', required=True,
        default='with_sale_taxes')

    @api.model
    def _get_accounting_fields(self):
        return [
            field for field in self._fields
            if self._fields[field].comodel_name and
            self._fields[field].comodel_name in
            ('account.account', 'account.journal')
        ]

    @api.one
    @api.constrains('asset_journal_id', 'asset_account_id',
                    'asset_analytic_account_id', 'depreciation_journal_id',
                    'accounting_depreciation_account_id',
                    'accounting_depreciation_expense_account_id',
                    'accounting_depreciation_income_account_id',
                    'exceptional_depreciation_account_id',
                    'exceptional_depreciation_expense_account_id',
                    'exceptional_depreciation_income_account_id',
                    'sale_journal_id', 'sale_receivable_account_id',
                    'sale_expense_account_id', 'sale_income_account_id',
                    'sale_analytic_account_id')
    def _check_accounting_fields(self):
        for field in self._get_accounting_fields():
            if self[field] and self[field].company_id != self.company_id:
                raise ValidationError(
                    _('Accounts and journals must be linked to '
                      'the same company as asset category'))

    @api.one
    @api.constrains('accounting_rate', 'fiscal_rate')
    def _check_depreciation_rates(self):
        for field in ('accounting_rate', 'fiscal_rate'):
            rate = self[field]
            if rate < 0.0 or rate > 100.0:
                raise ValidationError(
                    _('Amortization rates must be percentages!'))

    @api.onchange('asset_in_progress')
    def _onchange_asset_in_progress(self):
        if self.asset_in_progress:
            self.accounting_method = 'none'
            self.fiscal_method = 'none'

    @api.one
    def name_get(self):
        return self.id, '[%s] %s' % (self.code, self.name)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        domain = [('name', operator, name), ('code', operator, name)]
        if operator not in expression.NEGATIVE_TERM_OPERATORS:
            domain = ['|'] + domain
        recs = self.search(domain + (args or []), limit=limit)
        return recs.name_get()

    @api.multi
    def copy_data(self, default=None):
        self.ensure_one()
        default = default or {}
        default['name'] = _('%s Copy') % self.name
        return super(AccountAssetCategory, self).copy_data(default)

    @api.multi
    def write(self, vals):
        for category in self:
            old_vals = category.read(list(vals.keys()),
                                     load='_classic_write')[0]
            del old_vals['id']
            self.env['account.asset.asset'].change_accounts(
                '%s,%s' % (self._name, category.id), old_vals, vals)
        return super(AccountAssetCategory, self).write(vals)
