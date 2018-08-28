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

import decimal_precision as dp
from osv import orm, fields
from tools.translate import _

ASSET_CLASSES = [('tangible', 'Tangible'), ('intangible', 'Intangible')]


def _get_rates_visibility(obj, cr, uid, ids, name, arg, context=None):
    res = {}
    method_infos = obj.pool.get('account.asset.depreciation.method').get_method_infos(cr, uid)
    for resource in obj.browse(cr, uid, ids, context):
        res[resource.id] = {
            'accounting_rate_visibility': method_infos[resource.accounting_method]['use_manual_rate'],
            'fiscal_rate_visibility': method_infos[resource.fiscal_method]['use_manual_rate'],
        }
    return res


def _get_res_ids_from_depreciation_methods(obj, res_obj, cr, uid, ids, context=None):
        codes_by_type = {}
        for method in obj.browse(cr, uid, ids, context):
            codes_by_type.setdefault(method.depreciation_type, []).append(method.code)
        domain = []
        for type in codes_by_type:
            domain.append(('%s_method' % type, 'in', codes_by_type[type]))
        if len(domain) > 1:
            domain = ['|'] + domain
        return domain and res_obj.search(cr, uid, domain, context=context) or []


class AccountAssetCategory(orm.Model):
    _name = 'account.asset.category'
    _description = 'Asset Category'

    def _get_accounting_methods(self, cr, uid, context=None):
        return self.pool.get('account.asset.depreciation.method').get_methods_selection(cr, uid, 'accounting', context)

    def _get_fiscal_methods(self, cr, uid, context=None):
        return self.pool.get('account.asset.depreciation.method').get_methods_selection(cr, uid, 'fiscal', context)

    def _get_rates_visibility(self, cr, uid, ids, name, arg, context=None):
        return _get_rates_visibility(self, cr, uid, ids, name, arg, context=None)

    def _get_category_ids_from_depreciation_methods(self, cr, uid, ids, context=None):
        return _get_res_ids_from_depreciation_methods(self, self.pool.get('account.asset.category'), cr, uid, ids, context)

    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True),
        'code': fields.char('Code', size=32, required=True),
        'active': fields.boolean('Active'),
        'asset_class': fields.selection(ASSET_CLASSES, 'Asset Class', required=True),
        'asset_in_progress': fields.boolean(u'Assets in progress'),

        'company_id': fields.many2one('res.company', 'Company', select=True, required=True, ondelete='restrict',
                                      help="You cannot change company once an asset was posted."),

        'asset_journal_id': fields.many2one('account.journal', 'Asset Journal', required=True, ondelete='restrict'),
        'asset_account_id': fields.many2one('account.account', 'Asset Account', required=True, ondelete='restrict',
                                            domain=[('type', '!=', 'view')]),
        'asset_analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account', ondelete='restrict'),

        'depreciation_journal_id': fields.many2one('account.journal', 'Amortization Journal', required=False, ondelete='restrict',
                                                   help="Keep empty to use a unique journal for assets and amortizations"),
        'accounting_depreciation_account_id': fields.many2one('account.account', 'Amortization Account', required=False, ondelete='restrict',
                                                              domain=[('type', '!=', 'view')]),
        'accounting_depreciation_expense_account_id': fields.many2one('account.account', 'Amortization Expense Account', required=False,
                                                                      ondelete='restrict', domain=[('type', '!=', 'view')]),
        'accounting_depreciation_income_account_id': fields.many2one('account.account', 'Amortization Income Account', required=False,
                                                                     ondelete='restrict', domain=[('type', '!=', 'view')]),

        'exceptional_depreciation_account_id': fields.many2one('account.account', 'Depreciation Account', required=False, ondelete='restrict',
                                                               domain=[('type', '!=', 'view')]),
        'exceptional_depreciation_expense_account_id': fields.many2one('account.account', 'Depreciation Expense Account', required=False,
                                                                       ondelete='restrict', domain=[('type', '!=', 'view')]),
        'exceptional_depreciation_income_account_id': fields.many2one('account.account', 'Depreciation Income Account', required=False,
                                                                      ondelete='restrict', domain=[('type', '!=', 'view')]),

        'sale_journal_id': fields.many2one('account.journal', 'Disposal Journal', required=False, ondelete='restrict',
                                           help="Keep empty to use a unique journal for asset acquisition and disposal"),
        'sale_receivable_account_id': fields.many2one('account.account', 'Disposal Receivable Account', required=True, ondelete='restrict',
                                                      domain=[('type', '!=', 'view')]),
        'sale_expense_account_id': fields.many2one('account.account', 'Disposal Expense Account', required=True, ondelete='restrict',
                                                   domain=[('type', '!=', 'view')]),
        'sale_income_account_id': fields.many2one('account.account', 'Disposal Income Account', required=True, ondelete='restrict',
                                                  domain=[('type', '!=', 'view')]),
        'sale_analytic_account_id': fields.many2one('account.analytic.account', 'Disposal Analytic Account', ondelete='restrict'),

        'accounting_method': fields.selection(_get_accounting_methods, 'Accounting Method', required=True),
        'accounting_annuities': fields.integer('Accounting Annuities', required=False),
        'accounting_rate': fields.float('Accounting Amortization Rate (%)', digits=(4, 2)),
        'accounting_rate_visibility': fields.function(_get_rates_visibility, method=True, type='boolean', store={
            'account.asset.category': (lambda self, cr, uid, ids, context=None: ids, ['accounting_method'], 5),
            'account.asset.depreciation.method': (_get_category_ids_from_depreciation_methods, ['use_manual_rate'], 5),
        }, string='Accounting Amortization Rate Visibility', multi='rates_visibility'),

        'fiscal_method': fields.selection(_get_fiscal_methods, 'Fiscal Method', required=True),
        'fiscal_annuities': fields.integer('Fiscal Annuities', required=False),
        'fiscal_rate': fields.float('Fiscal Amortization Rate (%)', digits=(4, 2)),
        'fiscal_rate_visibility': fields.function(_get_rates_visibility, method=True, type='boolean', store={
            'account.asset.category': (lambda self, cr, uid, ids, context=None: ids, ['fiscal_method'], 5),
            'account.asset.depreciation.method': (_get_category_ids_from_depreciation_methods, ['use_manual_rate'], 5),
        }, string='Fiscal Amortization Rate Visibility', multi='rates_visibility'),

        'note': fields.text('Note'),

        'asset_ids': fields.one2many('account.asset.asset', 'category_id', 'Assets', readonly=True),
        'invoice_line_ids': fields.one2many('account.invoice.line', 'asset_category_id', 'Invoice Lines', readonly=True),

        'asset_creation': fields.selection([('auto', 'Automatic'), ('manual', 'Manual')], "Asset Creation", required=True,
                                           help="If automatic, an asset is created at invoice validation for each line associated "
                                                "to this asset category"),
        'confirm_asset': fields.boolean('Skip Draft State', help="Only in automatic mode"),

        'fiscal_deduction_limit': fields.float('Fiscal Deduction Limit', digits_compute=dp.get_precision('Account')),
        'tax_regularization_period': fields.integer('Tax Regularization Period', help="In years"),
        'tax_regularization_base': fields.selection([('deducted', 'Deducted'), ('undeducted', 'Undeducted')], 'Tax Regularization Base',
                                                    required=True),
        'tax_regularization_application': fields.selection([('with_sale_taxes', 'Taxed Sale'), ('without_sale_taxes', 'Untaxed Sale')],
                                                           'Tax Regularization Application', required=True),
    }

    def _get_default_company_id(self, cr, uid, context=None):
        return self.pool.get('res.company')._company_default_get(cr, uid, 'account.asset.category', context=context)

    _defaults = {
        'active': True,
        'company_id': _get_default_company_id,
        'asset_creation': 'auto',
        'accounting_annuities': 5,
        'accounting_rate': 25.0,
        'fiscal_method': 'none',
        'fiscal_annuities': 5,
        'fiscal_rate': 25.0,
        'tax_regularization_base': 'deducted',
        'tax_regularization_application': 'with_sale_taxes',
    }

    _sql_constraints = [
        ('uniq_code', 'unique(code, company_id)', u'Asset category code must be unique for a given company!'),
    ]

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        result = []
        for category in self.browse(cr, uid, ids, context):
            name = '%s - %s' % (category.code, category.name)
            result.append((category.id, name))
        return result

    @property
    def accounting_fields(self):
        return [k for k in self._columns if isinstance(self._columns[k], fields.many2one)
                and self._columns[k]._obj.startswith('account.')]

    def _check_companies(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for category in self.browse(cr, uid, ids, context):
            for column in self.accounting_fields:
                if getattr(category, column) and getattr(category, column).company_id != category.company_id:
                    return False
        return True

    def _check_depreciation_rates(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for category in self.browse(cr, uid, ids, context):
            for column in ('accounting_rate', 'fiscal_rate'):
                rate = getattr(category, column)
                if rate < 0.0 or rate > 100.0:
                    return False
        return True

    _constraints = [
        (_check_companies, 'Accounts and journal must be linked to the same company as asset category', ['accounting_fields']),
        (_check_depreciation_rates, 'Amortization rates must be percentages!', ['accounting_rate', 'fiscal_rate']),
        # TODO: ajouter des contraintes pour vérifier le bon remplissage des champs comptables
    ]

    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for category_id in ids:
            old_vals = self.read(cr, uid, category_id, vals.keys(), context, '_classic_write')
            del old_vals['id']
            self.pool.get('account.asset.asset').change_accounts(cr, uid, '%s,%s' % (self._name, category_id), old_vals, vals, context)
        return super(AccountAssetCategory, self).write(cr, uid, ids, vals, context)

    def copy_data(self, cr, uid, asset_category_id, default=None, context=None):
        default = default or {}
        default['name'] = _('%s Copy') % self.read(cr, uid, asset_category_id, ['name'], context)['name']
        for column in ('asset_ids', 'account_invoice_line_ids'):
            if column not in default:
                default[column] = []
        return super(AccountAssetCategory, self).copy_data(cr, uid, asset_category_id, default, context=context)

    def onchange_depreciation_method(self, cr, uid, ids, accounting_method, fiscal_method, context=None):
        res = {'value': {'accounting_rate_visibility': False, 'fiscal_rate_visibility': False}}
        if accounting_method == 'none':
            res['value']['fiscal_method'] = 'none'
        if accounting_method == 'manual' and fiscal_method not in ('none', 'manual'):
            res['value']['fiscal_method'] = 'manual'
        if accounting_method:
            method_infos = self.pool.get('account.asset.depreciation.method').get_method_infos(cr, uid)
            res['value']['accounting_rate_visibility'] = method_infos[accounting_method]['use_manual_rate']
            if fiscal_method:
                res['value']['fiscal_rate_visibility'] = method_infos[fiscal_method]['use_manual_rate']
        return res

    def onchange_asset_in_progress(self, cr, uid, ids, asset_in_progress, context=None):
        if asset_in_progress:
            return {'value': {'accounting_method': 'none', 'fiscal_method': 'none'}}
        return {}
