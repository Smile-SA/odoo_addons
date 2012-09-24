# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import orm, fields
from tools.translate import _

DEPRECIATION_METHODS = [('none', 'None'), ('linear', 'Linear'), ('degressive', 'Degressive')]
DEPRECIATION_FIELDS = ['method', 'periods', 'degressive_rate']
DEPRECIATION_TYPES = ['accounting', 'fiscal']
ALL_DEPRECIATION_FIELDS = ['%s_%s' % (depreciation_type, field) for field in DEPRECIATION_FIELDS for depreciation_type in DEPRECIATION_TYPES]
ACCOUNTING_FIELDS = ['asset_journal_id', 'asset_account_id', 'analytic_account_id', 'amortization_journal_id',
                     'amortization_account_id', 'amortization_expense_account_id',
                     'amortization_income_account_id', 'depreciation_account_id',
                     'depreciation_expense_account_id', 'depreciation_income_account_id']


def _compare_depreciation_terms(terms1, terms2):
    for column in DEPRECIATION_FIELDS:
        if column == 'degressive_rate' and terms1.get('method') == terms2.get('method') == 'linear':
            continue
        if terms1.get(column) != terms2.get(column):
            return False
    return True


def get_accelerated_depreciation(**kwargs):
    accounting_terms = dict([(column.replace('accounting_', ''), kwargs[column]) for column in kwargs if column.startswith('accounting_')])
    fiscal_terms = dict([(column.replace('fiscal_', ''), kwargs[column]) for column in kwargs if column.startswith('fiscal_')])
    if fiscal_terms.get('method') == 'none':
        return False
    return not _compare_depreciation_terms(accounting_terms, fiscal_terms)


class AccountAssetCategory(orm.Model):
    _name = 'account.asset.category'
    _description = 'Asset Category'

    def _get_accelerated_depreciation(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for category in self.read(cr, uid, ids, ALL_DEPRECIATION_FIELDS, context):
            res[category['id']] = get_accelerated_depreciation(**category)
        return res

    def _check_if_linked_assets_are_confirmed(self, cr, uid, ids, name, arg, context=None):
        res = {}.fromkeys(ids, False)
        for category in self.browse(cr, uid, ids, context):
            if [asset for asset in category.asset_ids if asset.state != 'draft'] \
                    or [invoice_line for invoice_line in category.invoice_line_ids
                        if invoice_line.invoice_id.state not in ('draft', 'proforma', 'proforma2')]:
                res[category.id] = True
        return res

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True, ondelete='restrict',
                                      help="You cannot change company once an asset was posted."),

        'asset_journal_id': fields.many2one('account.journal', 'Asset Journal', required=True, ondelete='restrict'),
        'asset_account_id': fields.many2one('account.account', 'Asset Account', required=True, ondelete='restrict',
                                            domain=[('type', '!=', 'view')]),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account', ondelete='restrict'),

        'amortization_journal_id': fields.many2one('account.journal', 'Amortization Journal', required=False, ondelete='restrict',
                                                   help="Keep empty to use a unique journal for assets and amortizations"),
        'amortization_account_id': fields.many2one('account.account', 'Amortization Account', required=False, ondelete='restrict',
                                                   domain=[('type', '!=', 'view')]),
        'amortization_expense_account_id': fields.many2one('account.account', 'Amortization Expense Account', required=False,
                                                           ondelete='restrict', domain=[('type', '!=', 'view')]),
        'amortization_income_account_id': fields.many2one('account.account', 'Amortization Income Account', required=False,
                                                          ondelete='restrict', domain=[('type', '!=', 'view')]),

        'depreciation_account_id': fields.many2one('account.account', 'Depreciation Account', required=False, ondelete='restrict',
                                                   domain=[('type', '!=', 'view')]),
        'depreciation_expense_account_id': fields.many2one('account.account', 'Depreciation Expense Account', required=False,
                                                           ondelete='restrict', domain=[('type', '!=', 'view')]),
        'depreciation_income_account_id': fields.many2one('account.account', 'Depreciation Income Account', required=False,
                                                          ondelete='restrict', domain=[('type', '!=', 'view')]),

        'disposal_receivable_account_id': fields.many2one('account.account', 'Disposal Receivable Account', required=True, ondelete='restrict',
                                                          domain=[('type', '!=', 'view')]),
        'disposal_expense_account_id': fields.many2one('account.account', 'Disposal Expense Account', required=True, ondelete='restrict',
                                                       domain=[('type', '!=', 'view')]),
        'disposal_income_account_id': fields.many2one('account.account', 'Disposal Income Account', required=True, ondelete='restrict',
                                                      domain=[('type', '!=', 'view')]),
        'disposal_analytic_account_id': fields.many2one('account.analytic.account', 'Disposal Analytic Account', ondelete='restrict'),

        'period_length': fields.integer('Period Length (in months)', required=False),

        'accounting_method': fields.selection(DEPRECIATION_METHODS, 'Computation Method', required=True),
        'accounting_periods': fields.integer('Number of Depreciations', required=False),
        'accounting_degressive_rate': fields.float('Degressive Rate (%)', digits=(4, 2)),
        'accounting_prorata': fields.boolean('Prorata Temporis', help='Indicates that the first depreciation entry for this asset have to be done '
                                             'from the purchase date instead of the first day of month'),

        'fiscal_method': fields.selection(DEPRECIATION_METHODS, 'Computation Method', required=True),
        'fiscal_periods': fields.integer('Number of Depreciations', required=False),
        'fiscal_degressive_rate': fields.float('Degressive Rate (%)', digits=(4, 2)),
        'fiscal_prorata': fields.boolean('Prorata Temporis'),

        'benefit_accelerated_depreciation': fields.function(_get_accelerated_depreciation, method=True, type='boolean',
                                                            string='Benefit Accelerated Depreciation'),
        'open_asset': fields.boolean('Skip Draft State'),
        'note': fields.text('Note'),

        'asset_ids': fields.one2many('account.asset.asset', 'category_id', 'Assets', readonly=True),
        'invoice_line_ids': fields.one2many('account.invoice.line', 'asset_category_id', 'Invoice Lines', readonly=True),

        'is_linked_to_confirmed_assets': fields.function(_check_if_linked_assets_are_confirmed, method=True, type='boolean',
                                                         string="Linked to confirmed assets"),

        'asset_creation': fields.selection([('auto', 'Automatic'), ('manual', 'Manual')], "Asset Creation", required=True,
                                           help="If automatic, an asset is created at invoice validation for each line associated "
                                                "to this asset category"),
    }

    def _get_default_company_id(self, cr, uid, context=None):
        return self.pool.get('res.company')._company_default_get(cr, uid, 'account.asset.category', context=context)

    _defaults = {
        'company_id': _get_default_company_id,
        'asset_creation': 'auto',
        'accounting_method': 'linear',
        'accounting_periods': 5,
        'period_length': 12,
        'accounting_degressive_rate': 25.0,
        'accounting_prorata': True,
        'fiscal_method': 'linear',
        'fiscal_periods': 5,
        'fiscal_degressive_rate': 25.0,
        'fiscal_prorata': False,
    }

    def _check_degressive_rates(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for category in self.browse(cr, uid, ids, context):
            for column in ('accounting_degressive_rate', 'fiscal_degressive_rate'):
                rate = getattr(category, column)
                if rate < 0.0 or rate > 100.0:
                    return False
        return True

    def _check_fiscal_depreciation_length(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for category in self.browse(cr, uid, ids, context):
            if category.accounting_method == 'none' or category.fiscal_method == 'none':
                continue
            if category.fiscal_periods > category.accounting_periods:
                return False
        return True

    def _check_period_length(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for category in self.browse(cr, uid, ids, context):
            if category.accounting_method == 'none':
                continue
            if category.period_length not in (1, 2, 3, 4, 6, 12):
                return False
        return True

    def _check_companies(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for category in self.browse(cr, uid, ids, context):
            for column in ACCOUNTING_FIELDS:
                if getattr(category, column) and getattr(category, column).company_id != category.company_id:
                    return False
        return True

    def _check_depreciation_length(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for category in self.browse(cr, uid, ids, context):
            if category.accounting_periods * category.period_length % 12:
                return False
        return True

    _constraints = [
        (_check_companies, 'Accounts and journal must be linked to the same company as asset category', ACCOUNTING_FIELDS),
        (_check_degressive_rates, 'Degressive rates must be percentages!', ['accounting_degressive_rate', 'fiscal_degressive_rate']),
        (_check_fiscal_depreciation_length, 'Fiscal depreciation must be faster than accounting depreciation!',
         ['accounting_periods', 'fiscal_periods']),
        (_check_period_length, 'Period length must be equal to 1, 2, 3, 4, 6 or 12 months!', ['period_length']),
        (_check_depreciation_length, 'Depreciation length must be a multiple of 12 (months)!', ['period_length', 'accounting_periods']),
    ]

    def onchange_accelerated_depreciation(self, cr, uid, ids, accounting_method, accounting_periods, accounting_degressive_rate, accounting_prorata,
                                          fiscal_method, fiscal_periods, fiscal_degressive_rate, fiscal_prorata, context=None):
        if fiscal_periods > accounting_periods:
            return {'warning': {
                'title': _('Warning'),
                'message': _('Fiscal depreciation must be faster than accounting depreciation!'),
            }}
        return {'value': {'benefit_accelerated_depreciation': get_accelerated_depreciation(**{
            'accounting_method': accounting_method,
            'accounting_periods': accounting_periods,
            'accounting_degressive_rate': accounting_degressive_rate,
            'accounting_prorata': accounting_prorata,
            'fiscal_method': fiscal_method,
            'fiscal_periods': fiscal_periods,
            'fiscal_degressive_rate': fiscal_degressive_rate,
            'fiscal_prorata': fiscal_prorata,
        })}}

    def onchange_accounting_method(self, cr, uid, ids, accounting_method, accounting_periods, accounting_degressive_rate,
                                   accounting_prorata, fiscal_method, fiscal_periods, fiscal_degressive_rate, fiscal_prorata, context=None):
        res = self.onchange_accelerated_depreciation(cr, uid, ids, accounting_method, accounting_periods, accounting_degressive_rate,
                                                     accounting_prorata, fiscal_method, fiscal_periods, fiscal_degressive_rate, fiscal_prorata,
                                                     context)
        if accounting_method == 'none':
            res.setdefault('value', {})['fiscal_method'] = 'none'
        return res

    def copy_data(self, cr, uid, asset_category_id, default=None, context=None):
        default = default or {}
        default['name'] = _('%s Copy') % self.read(cr, uid, asset_category_id, ['name'], context)['name']
        for column in ('asset_ids', 'account_invoice_line_ids'):
            if column not in default:
                default[column] = []
        return super(AccountAssetCategory, self).copy_data(cr, uid, asset_category_id, default, context=context)
