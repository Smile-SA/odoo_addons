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

from datetime import datetime
import logging
import time

import decimal_precision as dp
from openerp import SUPERUSER_ID
from osv import orm, fields
from tools.translate import _

from account_asset_category import _get_rates_visibility, _get_res_ids_from_depreciation_methods
from account_asset_tools import get_period_stop_date

ASSET_STATES = [
    ('draft', 'Draft'),
    ('confirm', 'Acquised Or In progress'),
    ('open', 'Into service'),
    ('close', 'Sold Or Scrapped'),
    ('cancel', 'Cancel'),
]
ASSET_TYPES = [
    ('purchase', 'Purchase'),
    ('purchase_refund', 'Purchase Refund'),
]
SALE_FIELDS = ['customer_id', 'sale_date', 'sale_account_date', 'sale_value', 'book_value', 'accumulated_amortization_value', 'sale_type',
               'sale_result', 'sale_result_short_term', 'sale_result_long_term', 'tax_regularization', 'regularization_tax_amount', 'is_out']

_logger = logging.getLogger('account.asset.asset')


class AccountAssetAsset(orm.Model):
    _name = 'account.asset.asset'
    _description = 'Asset'
    _parent_store = True

    def _get_accounting_methods(self, cr, uid, context=None):
        return self.pool.get('account.asset.depreciation.method').get_methods_selection(cr, uid, 'accounting', context)

    def _get_fiscal_methods(self, cr, uid, context=None):
        return self.pool.get('account.asset.depreciation.method').get_methods_selection(cr, uid, 'fiscal', context)

    def _get_book_value(self, cr, uid, ids, name, arg, context=None):
        # Book Value = Gross Value - Sum of accounting depreciations - Sum of exceptional depreciations
        res = {}
        for asset in self.browse(cr, uid, ids, context):
            book_value = asset.purchase_value
            for line in asset.depreciation_line_ids:
                if line.depreciation_type != 'fiscal' and (line.is_posted or line.move_id):
                    book_value -= line.depreciation_value
            res[asset.id] = book_value
        return res

    def _get_benefit_accelerated_depreciation(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if not ids:
            return res
        method_obj = self.pool.get('account.asset.depreciation.method')
        for asset in self.browse(cr, uid, ids, context):
            res[asset.id] = method_obj.get_benefit_accelerated_depreciation(cr, uid, asset.purchase_value, asset.salvage_value,
                                                                            asset.purchase_date, asset.in_service_date,
                                                                            asset.accounting_method, asset.accounting_annuities,
                                                                            asset.accounting_rate, asset.fiscal_method,
                                                                            asset.fiscal_annuities, asset.fiscal_rate, context)
        return res

    def _set_benefit_accelerated_depreciation(self, cr, uid, ids, name, value, arg, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        cr.execute('UPDATE account_asset_asset SET benefit_accelerated_depreciation = %s WHERE id IN %s', (value, tuple(ids)))
        return True

    def _get_tax_amount(self, cr, uid, amount_excl_tax, tax_ids, context=None):
        tax_obj = self.pool.get('account.tax')
        taxes = tax_obj.browse(cr, uid, tax_ids)
        amounts = tax_obj.compute_all(cr, uid, taxes, amount_excl_tax, 1.0)
        return amounts['total_included'] - amounts['total']

    def _get_purchase_tax_amount(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for asset in self.read(cr, uid, ids, ['purchase_tax_ids', 'purchase_value'], context):
            res[asset['id']] = self._get_tax_amount(cr, uid, asset['purchase_value'], asset['purchase_tax_ids'], context)
        return res

    def _get_sale_tax_amount(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for asset in self.read(cr, uid, ids, ['sale_tax_ids', 'sale_value'], context):
            res[asset['id']] = self._get_tax_amount(cr, uid, asset['sale_value'], asset['sale_tax_ids'], context)
        return res

    def _get_asset_accounts(self, cr, uid, ids, name, arg, context=None):
        res = {}
        category_obj = self.pool.get('account.asset.category')
        for asset in self.browse(cr, uid, ids, context):
            category = category_obj.browse(cr, uid, asset.category_id.id, {'force_company': asset.company_id.id})
            res[asset.id] = {
                'asset_account_id': category.asset_account_id.id,
                'sale_receivable_account_id': category.sale_receivable_account_id.id,
            }
        return res

    def _get_asset_ids_from_categories(self, cr, uid, ids, context=None):
        return self.pool.get('account.asset.asset').search(cr, uid, [('category_id', 'in', ids)], context=context)

    def _get_rates_visibility(self, cr, uid, ids, name, arg, context=None):
        return _get_rates_visibility(self, cr, uid, ids, name, arg, context=None)

    def _get_asset_ids_from_depreciation_methods(self, cr, uid, ids, context=None):
        return _get_res_ids_from_depreciation_methods(self, self.pool.get('account.asset.asset'), cr, uid, ids, context)

    def _get_asset_ids_from_depreciation_lines(self, cr, uid, ids, context=None):
        return list(set([line['asset_id'] for line in self.read(cr, uid, ids, ['asset_id'], context, '_classic_write')]))

    _columns = {
        'name': fields.char('Name', size=64, required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'code': fields.char('Reference', size=32, readonly=True),
        'state': fields.selection(ASSET_STATES, 'State', readonly=True),

        'parent_id': fields.many2one('account.asset.asset', 'Parent Asset', readonly=True, states={'draft': [('readonly', False)]},
                                     ondelete='restrict'),
        'child_ids': fields.one2many('account.asset.asset', 'parent_id', 'Child Assets'),
        'parent_left': fields.integer('Parent Left', readonly=True, select=True),
        'parent_right': fields.integer('Parent Right', readonly=True, select=True),
        'origin_id': fields.many2one('account.asset.asset', 'Origin Asset', readonly=True, ondelete='restrict'),

        'category_id': fields.many2one('account.asset.category', 'Asset Category', required=True, change_default=True, readonly=True,
                                       states={'draft': [('readonly', False)]}, ondelete='restrict'),
        'company_id': fields.related('category_id', 'company_id', type='many2one', relation='res.company', string='Company', store={
            'account.asset.asset': (lambda self, cr, uid, ids, context=None: ids, ['category_id'], 5),
            'account.asset.category': (_get_asset_ids_from_categories, ['company_id'], 5),
        }, ondelete='restrict', readonly=True),
        # CHANGE: allow to update anytime currency and offer a button to update asset after currency change, like in invoice form
        'currency_id': fields.many2one("res.currency", "Currency", required=True, ondelete='restrict', readonly=True,
                                       states={'draft': [('readonly', False)]}),

        'supplier_id': fields.many2one('res.partner', 'Supplier', required=True, readonly=True, states={'draft': [('readonly', False)]},
                                       ondelete='restrict', domain=[('supplier', '=', True)]),
        'purchase_date': fields.date('Purchase Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'purchase_value': fields.float('Gross Value', digits_compute=dp.get_precision('Account'), required=True, readonly=True,
                                       states={'draft': [('readonly', False)]}),
        'salvage_value': fields.float('Salvage Value', digits_compute=dp.get_precision('Account'),
                                      readonly=True, states={'draft': [('readonly', False)]}),
        'book_value': fields.function(_get_book_value, method=True, type='float', digits_compute=dp.get_precision('Account'), store={
            'account.asset.asset': (lambda self, cr, uid, ids, context=None: ids, ['purchase_value', 'salvage_value',
                                                                                   'accounting_method', 'is_out'], 5),
            'account.asset.depreciation.line': (_get_asset_ids_from_depreciation_lines, ['move_id'], 5),
        }, string='Book Value'),

        'accounting_method': fields.selection(_get_accounting_methods, 'Accounting Method', required=True,
                                              readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}),
        'accounting_annuities': fields.integer('Accounting Annuities', required=False, readonly=True,
                                               states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}),
        'accounting_rate': fields.float('Accounting Amortization Rate (%)', digits=(4, 2), readonly=True,
                                        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}),
        'accounting_rate_visibility': fields.function(_get_rates_visibility, method=True, type='boolean', store={
            'account.asset.asset': (lambda self, cr, uid, ids, context=None: ids, ['accounting_method'], 5),
            'account.asset.depreciation.method': (_get_asset_ids_from_depreciation_methods, ['use_manual_rate'], 5),
        }, string='Fiscal Amortization Rate Visibility', multi='rates_visibility'),

        'fiscal_method': fields.selection(_get_fiscal_methods, 'Fiscal Method', required=True,
                                          readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}),
        'fiscal_annuities': fields.integer('Fiscal Annuities', required=False, readonly=True,
                                           states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}),
        'fiscal_rate': fields.float('Fiscal Amortization Rate (%)', digits=(4, 2), readonly=True,
                                    states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}),
        'fiscal_rate_visibility': fields.function(_get_rates_visibility, method=True, type='boolean', store={
            'account.asset.asset': (lambda self, cr, uid, ids, context=None: ids, ['fiscal_method'], 5),
            'account.asset.depreciation.method': (_get_asset_ids_from_depreciation_methods, ['use_manual_rate'], 5),
        }, string='Fiscal Amortization Rate Visibility', multi='rates_visibility'),

        'benefit_accelerated_depreciation': fields.function(_get_benefit_accelerated_depreciation, method=True, type='boolean', store={
            'account.asset.asset': (lambda self, cr, uid, ids, context=None: ids, ['purchase_value', 'salvage_value',
                                                                                   'accounting_method', 'accounting_annuities', 'accounting_rate',
                                                                                   'fiscal_method', 'fiscal_annuities', 'fiscal_rate'], 5),
        }, string='Benefit Accelerated Depreciation', fnct_inv=_set_benefit_accelerated_depreciation, readonly=True,
            states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}),

        'in_service_date': fields.date('In-service Date', required=False, readonly=True,
                                       states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}),

        'depreciation_line_ids': fields.one2many('account.asset.depreciation.line', 'asset_id', 'Depreciation Lines', readonly=True),
        'accounting_depreciation_line_ids': fields.one2many('account.asset.depreciation.line', 'asset_id', 'Depreciation Lines', readonly=False,
                                                            domain=[('depreciation_type', '=', 'accounting')]),
        'fiscal_depreciation_line_ids': fields.one2many('account.asset.depreciation.line', 'asset_id', 'Depreciation Lines', readonly=False,
                                                        domain=[('depreciation_type', '=', 'fiscal')]),
        'exceptional_depreciation_line_ids': fields.one2many('account.asset.depreciation.line', 'asset_id', 'Depreciation Lines', readonly=True,
                                                             domain=[('depreciation_type', '=', 'exceptional')]),

        'quantity': fields.float('Quantity', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'uom_id': fields.many2one('product.uom', 'Unit of Measure', required=True, ondelete="restrict", readonly=True,
                                  states={'draft': [('readonly', False)]}),
        'purchase_tax_ids': fields.many2many('account.tax', 'account_asset_asset_account_tax_purchase_rel', 'asset_id', 'tax_id', 'Purchase Taxes',
                                             domain=[('parent_id', '=', False), ('type_tax_use', '!=', 'sale')],
                                             readonly=True, states={'draft': [('readonly', False)]}),
        'purchase_tax_amount': fields.function(_get_purchase_tax_amount, method=True, type='float',
                                               digits_compute=dp.get_precision('Account'), string="Tax Amount"),

        'asset_history_ids': fields.one2many('account.asset.history', 'asset_id', 'History', readonly=True),
        'account_move_line_ids': fields.one2many('account.move.line', 'asset_id', 'Account Move Lines', readonly=True),
        'invoice_line_ids': fields.one2many('account.invoice.line', 'asset_id', 'Invoice Lines', readonly=True),

        'asset_type': fields.selection(ASSET_TYPES, "Type", required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'note': fields.text('Note'),

        'customer_id': fields.many2one('res.partner', 'Customer', ondelete='restrict', domain=[('customer', '=', True)],
                                       readonly=True, states={'open': [('readonly', False)]}),
        'sale_date': fields.date('Sale Date', readonly=True, states={'open': [('readonly', False)]}),
        'sale_value': fields.float('Sale Value', digits_compute=dp.get_precision('Account'), readonly=True, states={'open': [('readonly', False)]}),
        'fiscal_book_value': fields.float('Fiscal Book Value', digits_compute=dp.get_precision('Account'), readonly=True),
        'accumulated_amortization_value': fields.float('Accumulated Amortization Value', digits_compute=dp.get_precision('Account'), readonly=True),
        'sale_type': fields.selection([('sale', 'Sale'), ('scrapping', 'Scrapping')], 'Disposal Type',
                                      readonly=True, states={'open': [('readonly', False)]}),
        'sale_result': fields.float('Sale Result', digits_compute=dp.get_precision('Account'), readonly=True),
        'sale_result_short_term': fields.float('Sale Result - Short Term', digits_compute=dp.get_precision('Account'), readonly=True),
        'sale_result_long_term': fields.float('Sale Result - Long Term', digits_compute=dp.get_precision('Account'), readonly=True),
        'sale_tax_ids': fields.many2many('account.tax', 'account_asset_asset_account_tax_sale_rel', 'asset_id', 'tax_id', 'Sale Taxes',
                                         domain=[('parent_id', '=', False), ('type_tax_use', '!=', 'purchase')], readonly=True,
                                         states={'open': [('readonly', False)]}),
        'sale_tax_amount': fields.function(_get_sale_tax_amount, method=True, type='float',
                                           digits_compute=dp.get_precision('Account'), string="Tax Amount"),
        'sale_invoice_number': fields.char('Invoice Number', size=64),
        'tax_regularization': fields.boolean('Tax regularization', readonly=True),
        'regularization_tax_amount': fields.float('Tax amount to regularize', digits_compute=dp.get_precision('Account'), readonly=True),
        'is_out': fields.boolean('Is Out Of Heritage'),

        'number': fields.related('invoice_line_ids', 'invoice_id', 'move_id', 'name', type='char', size=64, readonly=True,
                                 store=False, string='Number'),

        # TODO: un changement de comptes doit engendrer une extourne comptable, un fields.function semble donc peu compatible
        'asset_account_id': fields.function(_get_asset_accounts, method=True, type='many2one', relation='account.account', store={
            'account.asset.asset': (lambda self, cr, uid, ids, context=None: ids, ['category_id'], 5),
            'account.asset.category': (_get_asset_ids_from_categories, ['asset_account_id'], 5),
        }, string='Asset Account', readonly=True, multi="accounts"),
        'sale_receivable_account_id': fields.function(_get_asset_accounts, method=True, type='many2one', store={
            'account.asset.asset': (lambda self, cr, uid, ids, context=None: ids, ['category_id'], 5),
            'account.asset.category': (_get_asset_ids_from_categories, ['sale_receivable_account_id'], 5),
        }, relation='account.account', string='Disposal Receivable Account', readonly=True, multi="accounts"),

        'purchase_account_date': fields.date('Accounting date for purchase', readonly=True, states={'draft': [('readonly', False)]},
                                             help="Keep empty to use the current date"),
        'sale_account_date': fields.date('Accounting date for sale', readonly=True, states={'open': [('readonly', False)]},
                                         help="Keep empty to use the current date"),

        'purchase_move_id': fields.many2one('account.move', 'Purchase Account Move', readonly=True),
        'sale_move_id': fields.many2one('account.move', 'Sale Account Move', readonly=True),
        'purchase_cancel_move_id': fields.many2one('account.move', 'Purchase Cancellation Account Move', readonly=True),
        'sale_cancel_move_id': fields.many2one('account.move', 'Sale Cancellation Account Move', readonly=True),
    }

    def _get_default_code(self, cr, uid, context=None):
        return self.pool.get('ir.sequence').get(cr, uid, 'account.asset.asset', context)

    def _get_default_uom_id(self, cr, uid, context=None):
        try:
            return self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'product_uom_unit')[1]
        except ValueError:
            return False

    _defaults = {
        'state': 'draft',
        'asset_type': 'purchase',
        'quantity': 1.0,
        'uom_id': _get_default_uom_id,
    }

    def _check_recursion(self, cr, uid, ids, context=None, parent=None):
        return super(AccountAssetAsset, self)._check_recursion(cr, uid, ids, context=context, parent=parent)

    def _check_rates(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for asset in self.browse(cr, uid, ids, context):
            for field in ('accounting_rate', 'fiscal_rate'):
                rate = getattr(asset, field)
                if rate < 0.0 or rate > 100.0:
                    return False
        return True

    def _check_asset(self, cr, uid, ids, check_expression, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for asset in self.browse(cr, uid, ids, context):
            if eval(check_expression, {'asset': asset}):
                return False
        return True

    def _check_asset_type(self, cr, uid, ids, context=None):
        return self._check_asset(cr, uid, ids, "asset.asset_type == 'purchase_refund' and not asset.parent_id", context)

    def _check_quantity(self, cr, uid, ids, context=None):
        return self._check_asset(cr, uid, ids, "asset.quantity < 0.0", context)

    def _check_purchase_value(self, cr, uid, ids, context=None):
        return self._check_asset(cr, uid, ids, "asset.purchase_value < 0.0", context)

    def _check_salvage_value(self, cr, uid, ids, context=None):
        return self._check_asset(cr, uid, ids, "asset.salvage_value < 0.0 or asset.salvage_value > asset.purchase_value", context)

    _constraints = [
        (_check_recursion, 'You cannot create recursive assets!', ['parent_id']),
        (_check_rates, 'Amortization rates must be percentages!', ['accounting_rate', 'fiscal_rate']),
        (_check_asset_type, 'Purchase refund is possible only for secondary assets', ['asset_type']),
        (_check_quantity, 'Quantity cannot be negative!', ['quantity']),
        (_check_purchase_value, 'Gross value cannot be negative!', ['purchase_value']),
        (_check_salvage_value, 'Salvage value cannot be negative nor bigger than gross value!', ['salvage_value', 'purchase_value']),
    ]

    def name_get(self, cr, uid, ids, context=None):
        res = {}
        for asset in self.browse(cr, uid, ids, context):
            res[asset.id] = asset.name
            if asset.code:
                res[asset.id] = '[%s] %s' % (asset.code, asset.name)
        return res.items()

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        domain = ['|', ('code', operator, name), ('name', operator, name)] + (args or [])
        ids = self.search(cr, uid, domain, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def create(self, cr, uid, vals, context=None):
        if not vals.get('fiscal_method'):
            vals['fiscal_method'] = 'none'
        asset_id = super(AccountAssetAsset, self).create(cr, uid, vals, context)
        fields_to_compute = [field for field in self._columns if isinstance(self._columns[field], (fields.function, fields.related))
                             and self._columns[field].store]
        self._store_set_values(cr, uid, [asset_id], fields_to_compute, context)
        return asset_id

    def copy_data(self, cr, uid, asset_id, default=None, context=None):
        default = default or {}
        default['name'] = _("%s Copy") % self.read(cr, uid, asset_id, ['name'], context)['name']
        default['code'] = self._get_default_code(cr, uid, context)
        if 'state' not in default:
            default['state'] = 'draft'
        if 'purchase_account_date' not in default:
            default['purchase_account_date'] = False
        if 'origin_id' not in default:
            default['origin_id'] = False
        for field in ('accounting_depreciation_line_ids', 'fiscal_depreciation_line_ids', 'depreciation_line_ids', 'sale_tax_ids',
                      'invoice_line_ids', 'account_move_line_ids', 'asset_history_ids', 'child_ids', 'exceptional_depreciation_line_ids'):
            if field not in default:
                default[field] = [(6, 0, [])]
        for field in SALE_FIELDS:
            if field not in default:
                default[field] = False
        return super(AccountAssetAsset, self).copy_data(cr, uid, asset_id, default, context=context)

    def onchange_depreciation_params(self, cr, uid, ids, purchase_value, salvage_value,
                                     purchase_date, in_service_date,
                                     accounting_method, accounting_annuities, accounting_rate,
                                     fiscal_method, fiscal_annuities, fiscal_rate, context=None):
        if not (accounting_method and fiscal_method and accounting_annuities and fiscal_annuities):
            return {}
        method_obj = self.pool.get('account.asset.depreciation.method')
        benefit = method_obj.get_benefit_accelerated_depreciation(cr, uid, purchase_value, salvage_value, purchase_date, in_service_date,
                                                                  accounting_method, accounting_annuities, accounting_rate,
                                                                  fiscal_method, fiscal_annuities, fiscal_rate, context)
        res = {'value': {'benefit_accelerated_depreciation': benefit}}
        res['value'].update(self.pool.get('account.asset.category').onchange_depreciation_method(cr, uid, ids, accounting_method,
                                                                                                 fiscal_method, context)['value'])
        return res

    def onchange_category_id(self, cr, uid, ids, category_id, context=None):
        res = {'value': {}}
        if category_id:
            fields_to_read = ['accounting_method', 'accounting_annuities', 'accounting_rate',
                              'fiscal_method', 'fiscal_annuities', 'fiscal_rate',
                              'company_id']
            category = self.pool.get('account.asset.category').read(cr, uid, category_id, fields_to_read, context, '_classic_write')
            for field in fields_to_read:
                res['value'][field] = category[field]
        return res

    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        res = {'value': {}}
        if company_id:
            res['value']['currency_id'] = self.pool.get('res.company').browse(cr, uid, company_id, context).currency_id.id
        return res

    def _get_depreciation_start_date(self, cr, uid, asset, depreciation_type, context=None):
        method_obj = self.pool.get('account.asset.depreciation.method')
        method_info = method_obj.get_method_info(cr, uid, getattr(asset, '%s_method' % depreciation_type))
        if method_info['depreciation_start_date'] == 'first_day_of_purchase_month':
            depreciation_start_date = '%s-01' % asset.purchase_date[':-3']
        else:
            depreciation_start_date = asset.in_service_date
        return datetime.strptime(depreciation_start_date, '%Y-%m-%s')

    def _get_depreciation_arguments(self, cr, uid, asset_id, depreciation_type, context=None):
        asset = self.browse(cr, uid, asset_id, context)
        method = getattr(asset, '%s_method' % depreciation_type)
        depreciation_period = asset.company_id.depreciation_period
        fiscalyear_start_day = self.pool.get('res.company').get_fiscalyear_start_day(cr, uid, asset.company_id.id, context)
        readonly_values = {}
        exceptional_values = {}
        for line in asset.depreciation_line_ids:
            period_stop_month = get_period_stop_date(line.depreciation_date, fiscalyear_start_day,
                                                     asset.company_id.depreciation_period).strftime('%Y-%m')
            if line.depreciation_type == depreciation_type and (line.is_posted or method == 'manual'):
                readonly_values.setdefault(period_stop_month, {'depreciation_value': 0.0, 'base_value': 0.0})
                readonly_values[period_stop_month]['depreciation_value'] += line.depreciation_value
                readonly_values[period_stop_month]['base_value'] = line.base_value
            elif line.depreciation_type == 'exceptional':
                exceptional_values.setdefault(period_stop_month, 0.0)
                exceptional_values[period_stop_month] += line.depreciation_value
        method_obj = self.pool.get('account.asset.depreciation.method')
        accounting_stop_date = method_obj.get_depreciation_stop_date(cr, uid, asset.accounting_method, asset.purchase_date,
                                                                     asset.in_service_date, asset.accounting_annuities,
                                                                     depreciation_period, fiscalyear_start_day, exceptional_values)
        fiscal_stop_date = method_obj.get_depreciation_stop_date(cr, uid, asset.fiscal_method, asset.purchase_date,
                                                                 asset.in_service_date, asset.fiscal_annuities,
                                                                 depreciation_period, fiscalyear_start_day, exceptional_values)
        board_stop_date = max(accounting_stop_date, fiscal_stop_date)
        return {
            'code': method,
            'purchase_value': asset.purchase_value,
            'salvage_value': asset.salvage_value,
            'annuities': getattr(asset, '%s_annuities' % depreciation_type),
            'rate': getattr(asset, '%s_rate' % depreciation_type),
            'purchase_date': asset.purchase_date,
            'in_service_date': asset.in_service_date,
            'sale_date': asset.sale_date,
            'depreciation_period': depreciation_period,
            'fiscalyear_start_day': fiscalyear_start_day,
            'rounding': len(str(asset.currency_id.rounding).split('.')[-1]),
            'board_stop_date': board_stop_date,
            'readonly_values': readonly_values,
            'exceptional_values': exceptional_values,
            'context': context,
        }

    def _update_or_create_depreciation_lines(self, cr, uid, asset_id, line_infos, depreciation_type, context=None):
        asset = self.browse(cr, SUPERUSER_ID, asset_id, context)
        is_manual = getattr(asset, '%s_method' % depreciation_type)
        lines_to_create = []
        for vals in line_infos:
            vals.update({
                'asset_id': asset.id,
                'depreciation_type': depreciation_type,
                'depreciation_date': vals['depreciation_date'].strftime('%Y-%m-%d'),
            })
            readonly = vals['readonly']
            del vals['readonly']
            if readonly:
                if is_manual:
                    for dline in getattr(asset, '%s_depreciation_line_ids' % depreciation_type):
                        if dline.depreciation_date == vals['depreciation_date']:
                            dline.write(vals)
                            break
                continue
            lines_to_create.append(vals)
        if lines_to_create:
            self.pool.get('account.asset.depreciation.line').bulk_create(cr, SUPERUSER_ID, lines_to_create, context)
        return True

    def _compute_depreciation_lines(self, cr, uid, asset_id, depreciation_type='accounting', context=None):
        depreciation_line_obj = self.pool.get('account.asset.depreciation.line')
        # Delete old lines
        line_ids_to_delete = depreciation_line_obj.search(cr, uid, [('asset_id', '=', asset_id),
                                                                    ('depreciation_type', '=', depreciation_type),
                                                                    ('is_posted', '=', False),
                                                                    ('asset_id.%s_method' % depreciation_type, '!=', 'manual')], context=context)
        depreciation_line_obj.unlink(cr, SUPERUSER_ID, line_ids_to_delete, context)
        # Create new lines
        kwargs = self._get_depreciation_arguments(cr, uid, asset_id, depreciation_type, context)
        line_infos = self.pool.get('account.asset.depreciation.method').compute_depreciation_board(cr, uid, **kwargs)
        return self._update_or_create_depreciation_lines(cr, uid, asset_id, line_infos, depreciation_type, context)

    def compute_depreciation_board(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for asset_id in ids:
            self._compute_depreciation_lines(cr, uid, asset_id, 'accounting', context)
            self._compute_depreciation_lines(cr, uid, asset_id, 'fiscal', context)
        return True

    def confirm_asset_purchase(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        asset_ids_with_purchase_account_date = [asset.id for asset in self.browse(cr, uid, ids, context)
                                                if asset.purchase_account_date]
        vals = {'state': 'confirm', 'code': self._get_default_code(cr, uid, context)}
        if asset_ids_with_purchase_account_date:
            self.write(cr, uid, asset_ids_with_purchase_account_date, vals, context)
        asset_ids_without_purchase_account_date = list(set(ids) - set(asset_ids_with_purchase_account_date))
        if asset_ids_without_purchase_account_date:
            vals['purchase_account_date'] = time.strftime('%Y-%m-%d')
            self.write(cr, uid, asset_ids_without_purchase_account_date, vals, context)
        return True

    def button_confirm_asset_purchase(self, cr, uid, ids, context=None):
        return self.confirm_asset_purchase(cr, uid, ids, context)

    def _can_cancel_asset_purchase(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for asset in self.browse(cr, uid, ids, context):
            if asset.state == 'cancel':
                raise orm.except_orm(_('Error'), _('You cannot cancel a canceled asset!'))
            if asset.state == 'close':
                raise orm.except_orm(_('Error'), _('You cannot cancel a disposed asset!'))

    def cancel_asset_purchase(self, cr, uid, ids, context=None):
        # TODO: cancel automatically children ?
        self._can_cancel_asset_purchase(cr, uid, ids, context)
        return self.write(cr, uid, ids, {'state': 'cancel', 'invoice_line_ids': [(5,)]}, context)

    def button_cancel_asset_purchase(self, cr, uid, ids, context=None):
        return self.cancel_asset_purchase(cr, uid, ids, context)

    def _can_validate(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for asset in self.browse(cr, uid, ids, context):
            if asset.category_id.asset_in_progress or not asset.in_service_date:
                raise orm.except_orm(_('Error'), _('You cannot validate an asset in progress or an asset without in-service date!'))
            if asset.state == 'draft':
                raise orm.except_orm(_('Error'), _('Please confirm this asset before validating it!'))

    def validate(self, cr, uid, ids, context=None):
        self._can_validate(cr, uid, ids, context)
        self.compute_depreciation_board(cr, uid, ids, context)
        return self.write(cr, uid, ids, {'state': 'open'}, context)

    def button_validate(self, cr, uid, ids, context=None):
        self.validate(cr, uid, ids, context)
        return {'type': 'ir.actions.act_window_close'}

    def button_put_into_service(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'ids must be a list with only one item!'
        context_copy = context and context.copy() or {}
        context_copy['default_asset_id'] = ids[0]
        context_copy['asset_validation'] = True
        return {
            'name': _('Asset Update'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.asset.history',
            'target': 'new',
            'context': context_copy,
        }

    def button_modify(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'ids must be a list with only one item!'
        context_copy = context and context.copy() or {}
        context_copy['default_asset_id'] = ids[0]
        return {
            'name': _('Asset Update'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.asset.history',
            'target': 'new',
            'context': context_copy,
        }

    def button_split(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'ids must be a list with only one item!'
        context_copy = context and context.copy() or {}
        asset_info = self.read(cr, uid, ids[0], ['purchase_value', 'salvage_value', 'quantity'], context)
        context_copy.update({
            'default_asset_id': asset_info['id'],
            'default_initial_purchase_value': asset_info['purchase_value'],
            'default_initial_salvage_value': asset_info['salvage_value'],
            'default_initial_quantity': asset_info['quantity'],
            'default_purchase_value': asset_info['purchase_value'],
            'default_salvage_value': asset_info['salvage_value'],
            'default_quantity': asset_info['quantity'],
        })
        return {
            'name': _('Asset Split'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.asset.split_wizard',
            'target': 'new',
            'context': context_copy,
        }

    def button_sell(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'ids must be a list with only one item!'
        return {
            'name': _('Asset Sale/Scrapping'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.pool.get('ir.model.data').get_object_reference(cr, uid, 'smile_account_asset', 'view_account_asset_asset_sale_form')[1],
            'res_model': 'account.asset.asset',
            'res_id': ids[0],
            'target': 'new',
            'context': context,
        }

    def _get_fiscal_book_value(self, cr, uid, asset, context=None):
        # Fiscal Book Value = Gross Value - Sum of fiscal depreciations (accounting_depreciation_value + fiscal_accelerated_value)
        fiscal_book_value = asset.purchase_value
        if asset.accounting_depreciation_line_ids:
            fiscal_book_value -= sum([depr.depreciation_value for depr in asset.accounting_depreciation_line_ids], 0.0)
            if asset.benefit_accelerated_depreciation and asset.fiscal_depreciation_line_ids:
                fiscal_book_value -= sum([depr.accelerated_value for depr in asset.fiscal_depreciation_line_ids], 0.0)
        return fiscal_book_value

    def _get_regularization_tax_coeff(self, cr, uid, asset, context=None):
        # TODO: gérer les coeff de déduction à l'achat et à la vente
        regularization_tax_coeff = 0.0
        if asset.purchase_tax_ids:
            apply_regulatization = bool(asset.sale_tax_ids) if asset.category_id.tax_regularization_application == 'with_sale_taxes' \
                else not asset.sale_tax_ids
            regularization_period = asset.category_id.tax_regularization_period
            if apply_regulatization and 0.0 <= int(time.strftime('%Y')) - int(asset.purchase_date[:4]) < regularization_period:
                method_obj = self.pool.get('account.asset.depreciation.method')
                depreciation_start_date = method_obj.get_depreciation_start_date(cr, uid, asset.accounting_method,
                                                                                 asset.purchase_date, asset.in_service_date, context)
                # TODO: revoir cela afin de prendre en compte les années ne commençant pas le 1er janvier
                remaining_years = regularization_period - (int(asset.sale_date[:4]) - int(depreciation_start_date[:4]) + 1)
                if remaining_years > 0:
                    regularization_tax_coeff = float(remaining_years) / regularization_period
        return regularization_tax_coeff

    def _get_regularization_tax_amount(self, cr, uid, asset, context=None):
        coeff = self._get_regularization_tax_coeff(cr, uid, asset, context)
        tax = asset.category_id.tax_regularization_base == 'deducted' and asset.purchase_tax_amount or 0.0
        return tax * coeff

    def get_sale_infos(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = {}
        today = time.strftime('%Y-%m-%d')
        for asset in self.browse(cr, uid, ids, context):
            fiscal_book_value = self._get_fiscal_book_value(cr, uid, asset, context)
            regularization_tax_amount = self._get_regularization_tax_amount(cr, uid, asset, context)
            fiscal_sale_result = asset.sale_value - fiscal_book_value - regularization_tax_amount
            accumulated_amortization_value = asset.purchase_value - fiscal_book_value
            res[asset.id] = {
                'tax_regularization': bool(regularization_tax_amount),
                'regularization_tax_amount': regularization_tax_amount,
                'sale_result': fiscal_sale_result,
                'sale_result_short_term': min(fiscal_sale_result, accumulated_amortization_value),
                'sale_result_long_term': fiscal_sale_result > accumulated_amortization_value and
                fiscal_sale_result - accumulated_amortization_value or 0.0,
                'fiscal_book_value': fiscal_book_value,
                'accumulated_amortization_value': accumulated_amortization_value,
                'sale_account_date': asset.sale_account_date or today,
            }
        return res

    def _can_confirm_asset_sale(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for asset in self.browse(cr, uid, ids, context=None):
            if asset.state not in ('confirm', 'open'):
                raise orm.except_orm(_('Error'), _('You cannot dispose a %s asset') % dict(ASSET_STATES)[asset.state])
            if asset.sale_type == 'scrapping' and asset.sale_value:
                raise orm.except_orm(_('Error'), _("Scrapping value must be null"))

    def confirm_asset_sale(self, cr, uid, ids, context=None):
        self._can_confirm_asset_sale(cr, uid, ids, context)
        self.compute_depreciation_board(cr, uid, ids, context)
        sale_infos_by_asset = self.get_sale_infos(cr, uid, ids, context)
        for asset_id in sale_infos_by_asset:
            self.write(cr, uid, asset_id, sale_infos_by_asset[asset_id], context)
        return self.write(cr, uid, ids, {'state': 'close'}, context)

    def button_confirm_asset_sale(self, cr, uid, ids, context=None):
        self.confirm_asset_sale(cr, uid, ids, context)
        return {'type': 'ir.actions.act_window_close'}

    def _can_cancel_asset_sale(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for asset in self.browse(cr, uid, ids, context):
            if asset.state != 'close':
                raise orm.except_orm(_('Error'), _('You cannot cancel the disposal of an asset not disposed!'))

    def cancel_asset_sale(self, cr, uid, ids, context=None):
        # TODO: gérer les annulations des ventes liées parent-enfant
        self._can_cancel_asset_sale(cr, uid, ids, context)
        vals = dict([(field, False) for field in SALE_FIELDS])
        self.write(cr, uid, ids, vals, context)
        return self.validate(cr, uid, ids, context)

    def button_cancel_asset_sale(self, cr, uid, ids, context=None):
        return self.cancel_asset_sale(cr, uid, ids, context)

    def _can_output(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for asset in self.browse(cr, uid, ids, context=None):
            if asset.state != 'close':
                raise orm.except_orm(_('Error'), _('You cannot output an asset not already disposed!'))
            if asset.is_out:
                raise orm.except_orm(_('Error'), _('You cannot output an asset already out!'))

    def output(self, cr, uid, ids, context=None):
        self._can_output(cr, uid, ids, context)
        return self.write(cr, uid, ids, {'is_out': True}, context)

    def button_output(self, cr, uid, ids, context=None):
        return self.output(cr, uid, ids, context)

    def run_tests(self):
        "Call from module test/run_tests.yml"
        import run_tests
        run_tests.main()
