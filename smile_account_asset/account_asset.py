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
from dateutil.relativedelta import relativedelta
import time

import decimal_precision as dp
from osv import orm, fields
from tools.translate import _

from account_asset_category import ALL_DEPRECIATION_FIELDS, DEPRECIATION_METHODS, get_accelerated_depreciation
from depreciation_board import DepreciationBoard, get_period_stop_date


ASSET_STATES = [('draft', 'Draft'), ('open', 'Running'), ('close', 'Sold Or Scrapped')]
ASSET_TYPES = [('purchase', 'Purchase'), ('purchase_refund', 'Purchase Refund')]


class AccountAssetAsset(orm.Model):
    _name = 'account.asset.asset'
    _description = 'Asset'
    _parent_store = True

    def _get_depreciation_infos(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if not ids:
            return res
        cr.execute("SELECT asset_id as id, round(sum(debit-credit)) as amount "
                   "FROM account_move_line WHERE asset_id IN %s GROUP BY asset_id", (tuple(ids),))
        res.update(dict(cr.fetchall()))
        company_obj = self.pool.get('res.company')
        fields_to_read = ['purchase_value', 'salvage_value', 'depreciation_date_start', 'sale_value', 'state',
                          'period_length', 'accounting_prorata', 'company_id']
        fields_to_read += ALL_DEPRECIATION_FIELDS
        for asset in self.read(cr, uid, ids, fields_to_read, context, '_classic_write'):
            fiscalyear_start_day = company_obj.get_fiscalyear_start_day(cr, uid, asset['company_id'], context)
            accelerated_depreciation = get_accelerated_depreciation(**asset)
            if asset['state'] == 'draft':
                book_value = asset['purchase_value']
            elif asset['state'] == 'open':
                book_value = res.get(asset['id'], 0.0)
            else:
                book_value = asset['salvage_value']
            depreciation_date_stop = datetime.strptime(asset['depreciation_date_start'], '%Y-%m-%d')
            depreciation_date_stop += relativedelta(years=max(asset['accounting_periods'], asset['fiscal_periods']))
            res[asset['id']] = {
                'depreciation_date_stop': get_period_stop_date(depreciation_date_stop,
                                                               fiscalyear_start_day,
                                                               asset['period_length']).strftime('%Y-%m-%d'),
                'benefit_accelerated_depreciation': accelerated_depreciation,
                'amount_to_depreciate': book_value - asset['salvage_value'],
            }
        return res

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

    def _get_asset_ids_from_categories(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        return self.pool.get('account.asset.asset').search(cr, uid, [('category_id', 'in', ids), ('state', '=', 'draft')], context=context)

    _columns = {
        'name': fields.char('Name', size=64, required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'code': fields.char('Reference', size=32, readonly=True, states={'draft': [('readonly', False)]}),
        'state': fields.selection(ASSET_STATES, 'State', readonly=True),

        'parent_id': fields.many2one('account.asset.asset', 'Parent Asset', readonly=True, states={'draft': [('readonly', False)]},
                                     ondelete='cascade'),
        'child_ids': fields.one2many('account.asset.asset', 'parent_id', 'Children Assets'),
        'parent_left': fields.integer('Parent Left', readonly=True, select=True),
        'parent_right': fields.integer('Parent Right', readonly=True, select=True),

        'category_id': fields.many2one('account.asset.category', 'Asset Category', required=True, change_default=True, readonly=True,
                                       states={'draft': [('readonly', False)]}, ondelete='restrict'),
        'company_id': fields.many2one('res.company', 'Company', required=True, ondelete='restrict', readonly=True,
                                      states={'draft': [('readonly', False)]}),
        'currency_id': fields.related('company_id', 'currency_id', type="many2one", relation="res.currency", string="Currency", readonly=True,
                                      ondelete='restrict', store=True),

        'supplier_id': fields.many2one('res.partner', 'Supplier', required=True, readonly=True, states={'draft': [('readonly', False)]},
                                       ondelete='restrict', domain=[('supplier', '=', True)]),
        'purchase_date': fields.date('Purchase Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'purchase_value': fields.float('Gross Value', digits_compute=dp.get_precision('Account'), required=True, readonly=True,
                                       states={'draft': [('readonly', False)]}),
        'salvage_value': fields.float('Salvage Value', digits_compute=dp.get_precision('Account'),
                                      readonly=True, states={'draft': [('readonly', False)]}),
        'amount_to_depreciate': fields.function(_get_depreciation_infos, method=True, type='float', digits_compute=dp.get_precision('Account'),
                                                string='Amount to depreciate', multi='depreciation'),

        'accounting_method': fields.selection(DEPRECIATION_METHODS, 'Computation Method', required=True, readonly=True,
                                              states={'draft': [('readonly', False)]}),
        'accounting_periods': fields.integer('Depreciation Length (in years)', required=False, readonly=True,
                                             states={'draft': [('readonly', False)]}),
        'period_length': fields.integer('Period Length (in months)', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'accounting_degressive_rate': fields.float('Degressive Rate (%)', digits=(4, 2), readonly=True,
                                                   states={'draft': [('readonly', False)]}),
        'accounting_prorata': fields.boolean('Prorata Temporis', help='Indicates that the first depreciation entry for this asset have to be done '
                                             'from the purchase date instead of the first day of month', readonly=True,
                                             states={'draft': [('readonly', False)]}),

        'fiscal_method': fields.selection(DEPRECIATION_METHODS, 'Computation Method', required=True, readonly=True,
                                          states={'draft': [('readonly', False)]}),
        'fiscal_periods': fields.integer('Depreciation Length (in years)', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'fiscal_degressive_rate': fields.float('Degressive Rate (%)', digits=(4, 2), readonly=True, states={'draft': [('readonly', False)]}),
        'fiscal_prorata': fields.boolean('Prorata Temporis', readonly=True, states={'draft': [('readonly', False)]}),

        'benefit_accelerated_depreciation': fields.function(_get_depreciation_infos, method=True, type='boolean',
                                                            string='Benefit Accelerated Depreciation', multi='depreciation'),

        'depreciation_date_start': fields.date('Depreciation Start Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'depreciation_date_stop': fields.function(_get_depreciation_infos, method=True, type='date', string='Depreciation End Date',
                                                  multi='depreciation'),

        'depreciation_line_ids': fields.one2many('account.asset.depreciation.line', 'asset_id', 'Depreciation Lines', readonly=True),
        'accounting_depreciation_line_ids': fields.one2many('account.asset.depreciation.line', 'asset_id', 'Depreciation Lines', readonly=False,
                                                            domain=[('depreciation_type', '=', 'accounting')]),
        'fiscal_depreciation_line_ids': fields.one2many('account.asset.depreciation.line', 'asset_id', 'Depreciation Lines', readonly=False,
                                                        domain=[('depreciation_type', '=', 'fiscal')]),
        'exceptional_depreciation_line_ids': fields.one2many('account.asset.depreciation.line', 'asset_id', 'Depreciation Lines', readonly=True,
                                                             domain=[('depreciation_type', '=', 'exceptional')]),

        'validation_date': fields.date('Validation Date', readonly=True),

        'quantity': fields.float('Quantity', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'uom_id': fields.many2one('product.uom', 'Unit of Measure', required=True, ondelete="restrict", readonly=True,
                                  states={'draft': [('readonly', False)]}),
        'purchase_tax_ids': fields.many2many('account.tax', 'account_asset_asset_account_tax_purchase_rel', 'asset_id', 'tax_id', 'Taxes',
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
        'book_value': fields.float('Book Value', digits_compute=dp.get_precision('Account'), readonly=True),
        'accumulated_amortization_value': fields.float('Accumulated Amortization Value', digits_compute=dp.get_precision('Account'), readonly=True),
        'disposal_type': fields.selection([('sale', 'Sale'), ('scrapping', 'Scrapping')], 'Disposal Type',
                                          readonly=True, states={'open': [('readonly', False)]}),
        'sale_result': fields.float('Sale Result', digits_compute=dp.get_precision('Account'), readonly=True),
        'sale_result_short_term': fields.float('Sale Result - Short Term', digits_compute=dp.get_precision('Account'), readonly=True),
        'sale_result_long_term': fields.float('Sale Result - Long Term', digits_compute=dp.get_precision('Account'), readonly=True),
        'sale_tax_ids': fields.many2many('account.tax', 'account_asset_asset_account_tax_sale_rel', 'asset_id', 'tax_id', 'Taxes',
                                         domain=[('parent_id', '=', False), ('type_tax_use', '!=', 'sale')], readonly=True,
                                         states={'open': [('readonly', False)]}),
        'sale_tax_amount': fields.function(_get_sale_tax_amount, method=True, type='float',
                                           digits_compute=dp.get_precision('Account'), string="Tax Amount"),
        'regularization_tax_amount': fields.float('Tax amount to regularize', digits_compute=dp.get_precision('Account'), readonly=True),
        'is_out': fields.boolean('Is Out Of Heritage'),

        'asset_account_id': fields.related('category_id', 'asset_account_id', type='many2one', relation='account.account',
                                           string='Asset Account', readonly=True, store=True),
        'disposal_receivable_account_id': fields.related('category_id', 'disposal_receivable_account_id', type='many2one',
                                                         relation='account.account', string='Disposal Receivable Account',
                                                         readonly=True, store=True),

        'number': fields.related('invoice_line_ids', 'invoice_id', 'move_id', 'name', type='char', size=64, readonly=True,
                                 store=False, string='Number'),
    }

    def _get_default_company_id(self, cr, uid, context=None):
        return self.pool.get('res.company')._company_default_get(cr, uid, 'account.asset.category', context=context)

    def _get_default_code(self, cr, uid, context=None):
        return self.pool.get('ir.sequence').get(cr, uid, 'account.asset.asset', context)

    def _get_default_uom_id(self, cr, uid, context=None):
        try:
            return self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'product_uom_unit')[1]
        except ValueError:
            return False

    _defaults = {
        'company_id': _get_default_company_id,
        'code': _get_default_code,
        'state': 'draft',
        'depreciation_date_start': lambda *a: time.strftime('%Y-%m-%d'),
        'asset_type': 'purchase',
        'quantity': 1.0,
        'uom_id': _get_default_uom_id,
    }

    def _check_recursion(self, cr, uid, ids, context=None, parent=None):
        return super(AccountAssetAsset, self)._check_recursion(cr, uid, ids, context=context, parent=parent)

    def _check_degressive_rates(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for asset in self.browse(cr, uid, ids, context):
            for field in ('accounting_degressive_rate', 'fiscal_degressive_rate'):
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

    def _check_period_length(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for asset in self.browse(cr, uid, ids, context):
            if asset.accounting_method == 'none':
                continue
            if asset.period_length not in (1, 2, 3, 4, 6, 12):
                return False
        return True

    def _check_company(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for asset in self.browse(cr, uid, ids, context):
            if asset.company_id != asset.category_id.company_id:
                return False
        return True

    _constraints = [
        (_check_company, 'Asset must be linked to the same company as category', ['company_id', 'category_id']),
        (_check_recursion, 'You cannot create recursive assets!', ['parent_id']),
        (_check_degressive_rates, 'Degressive rates must be percentages!', ['accounting_degressive_rate', 'fiscal_degressive_rate']),
        (_check_asset_type, 'Purchase refund is possible only for secondary assets', ['asset_type']),
        (_check_quantity, 'Quantity cannot be negative!', ['quantity']),
        (_check_purchase_value, 'Gross value cannot be negative!', ['purchase_value']),
        (_check_salvage_value, 'Salvage value cannot be negative nor bigger than gross value!', ['salvage_value', 'purchase_value']),
        (_check_period_length, 'Period length must be equal to 1, 2, 3, 4, 6 or 12 months!', ['period_length']),
        # TODO: ajouter une contrainte afin de vérifier que le montant de l'immo correspond à la somme des lignes de facture à son origine
    ]

    def create(self, cr, uid, vals, context=None):
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
        if 'code' not in default:
            default['code'] = self.pool.get('ir.sequence').get(cr, uid, 'account.asset.asset', context)
        for field in ('accounting_depreciation_line_ids', 'fiscal_depreciation_line_ids', 'depreciation_line_ids', 'sale_tax_ids',
                      'invoice_line_ids', 'account_move_line_ids', 'asset_history_ids', 'child_ids', 'exceptional_depreciation_line_ids'):
            if field not in default:
                default[field] = [(6, 0, [])]
        for field in ('customer_id', 'sale_date', 'sale_value', 'book_value', 'accumulated_amortization_value', 'disposal_type', 'sale_result',
                      'sale_result_short_term', 'sale_result_long_term', 'regularization_tax_amount', 'is_out'):
            if field not in default:
                default[field] = False
        return super(AccountAssetAsset, self).copy_data(cr, uid, asset_id, default, context=context)

    def onchange_accelerated_depreciation(self, cr, uid, ids, accounting_method, accounting_periods, accounting_degressive_rate, accounting_prorata,
                                          fiscal_method, fiscal_periods, fiscal_degressive_rate, fiscal_prorata, context=None):
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

    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        res = {'value': {'currency_id': False}}
        if company_id:
            res['value']['currency_id'] = self.pool.get('res.company').read(cr, uid, company_id, ['currency_id'],
                                                                            context, '_classic_write')['currency_id']
        res['domain'] = {'category_id': [('company_id', '=', company_id)]}
        return res

    def onchange_category_id(self, cr, uid, ids, category_id, context=None):
        res = {'value': {}}
        if category_id:
            fields_to_read = ['benefit_accelerated_depreciation', 'company_id', 'period_length', 'accounting_prorata', 'fiscal_prorata']
            fields_to_read += ALL_DEPRECIATION_FIELDS
            category = self.pool.get('account.asset.category').read(cr, uid, category_id, fields_to_read, context, '_classic_write')
            for field in fields_to_read:
                res['value'][field] = category[field]
        return res

    def onchange_purchase_date(self, cr, uid, ids, purchase_date, context=None):
        res = {'value': {}}
        if purchase_date:
            res['value']['depreciation_date_start'] = purchase_date
        return res

    def _get_depreciation_arguments(self, cr, uid, asset_id, depreciation_type, context):
        asset = self.browse(cr, uid, asset_id, context)
        salvage_value = depreciation_type == 'accounting' and asset.salvage_value or 0.0
        method = getattr(asset, '%s_method' % depreciation_type)
        periods = getattr(asset, '%s_periods' % depreciation_type)
        degressive_rate = getattr(asset, '%s_degressive_rate' % depreciation_type)
        fiscalyear_start_day = self.pool.get('res.company').get_fiscalyear_start_day(cr, uid, asset.company_id.id, context)
        starts_on_first_day_of_month = not getattr(asset, '%s_prorata' % depreciation_type)
        readonly_values = {}
        exceptional_values = {}
        for line in asset.depreciation_line_ids:
            period_stop_month = get_period_stop_date(line.depreciation_date, fiscalyear_start_day, asset.period_length).strftime('%Y-%m')
            if line.depreciation_type == depreciation_type and (line.move_id or method == 'manual'):
                readonly_values.setdefault(period_stop_month, 0.0)
                readonly_values[period_stop_month] += line.depreciation_value
            elif line.depreciation_type == 'exceptional':
                exceptional_values.setdefault(period_stop_month, 0.0)
                exceptional_values[period_stop_month] += line.depreciation_value
        context = context or {}
        return {
            'gross_value': asset.purchase_value,
            'method': method,
            'years': periods,
            'degressive_rate': degressive_rate,
            'salvage_value': salvage_value,
            'depreciation_start_date': asset.depreciation_date_start,
            'starts_on_first_day_of_month': starts_on_first_day_of_month,
            'disposal_date': asset.sale_date or None,
            'period_length': asset.period_length,
            'readonly_values': readonly_values,
            'exceptional_values': exceptional_values,
            'fiscalyear_start_day': fiscalyear_start_day,
            'accounting_years': asset.accounting_periods,
            'rounding': len(str(asset.company_id.currency_id.rounding).split('.')[-1]),
            'depreciate_base_value': context.get('depreciate_%s_base_value' % depreciation_type),
        }

    def _update_or_create_depreciation_lines(self, cr, uid, asset_id, line_infos, depreciation_type, context):
        asset = self.browse(cr, uid, asset_id, context)
        for vals in line_infos:
            vals.update({
                'asset_id': asset.id,
                'depreciation_type': depreciation_type,
                'depreciation_date': vals['depreciation_date'].strftime('%Y-%m-%d'),
            })
            readonly = vals['readonly']
            del vals['readonly']
            if readonly:
                for dline in getattr(asset, '%s_depreciation_line_ids' % depreciation_type):
                    if dline.depreciation_date == vals['depreciation_date'] and \
                            (dline.move_id or getattr(dline.asset_id, '%s_method' % depreciation_type) == 'manual'):
                        dline.write(vals)
                        break
                continue
            self.pool.get('account.asset.depreciation.line').create(cr, uid, vals, context)
            vals['previous_accumulated_value'] = vals['accumulated_value'] - vals['depreciation_value']
        return True

    def _compute_depreciation_lines(self, cr, uid, asset_id, depreciation_type='accounting', context=None):
        depreciation_line_obj = self.pool.get('account.asset.depreciation.line')
        # Delete old lines

        line_ids_to_delete = depreciation_line_obj.search(cr, uid, [('asset_id', '=', asset_id),
                                                                    ('depreciation_type', '=', depreciation_type),
                                                                    ('move_id', '=', False),
                                                                    ('asset_id.%s_method' % depreciation_type, '!=', 'manual')], context=context)
        depreciation_line_obj.unlink(cr, uid, line_ids_to_delete, context)
        # Create new lines
        kwargs = self._get_depreciation_arguments(cr, uid, asset_id, depreciation_type, context)
        board = DepreciationBoard(**kwargs)
        line_infos = [line.__dict__ for line in board.compute()]
        return self._update_or_create_depreciation_lines(cr, uid, asset_id, line_infos, depreciation_type, context)

    def compute_depreciation_board(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for asset in self.read(cr, uid, ids, ['accounting_method', 'benefit_accelerated_depreciation'], context):
            if asset['accounting_method'] != 'none':
                self._compute_depreciation_lines(cr, uid, asset['id'], 'accounting', context)
                if asset['benefit_accelerated_depreciation']:
                    self._compute_depreciation_lines(cr, uid, asset['id'], 'fiscal', context)
        return True

    def validate(self, cr, uid, ids, context=None):
        self.compute_depreciation_board(cr, uid, ids, context)
        return self.write(cr, uid, ids, {'state': 'open'}, context)

    def button_validate(self, cr, uid, ids, context=None):
        self.validate(cr, uid, ids, context)
        return self.write(cr, uid, ids, {'state': 'open', 'validation_date': time.strftime('%Y-%m-%d')}, context)

    def button_modify(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'ids must be a list with only one item!'
        context_copy = (context or {}).copy()
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
        context_copy = (context or {}).copy()
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

    def _get_book_value_at_disposal(self, cr, uid, asset, context=None):
        book_value = asset.purchase_value
        if asset.accounting_depreciation_line_ids:
            book_value = asset.accounting_depreciation_line_ids[-1].book_value
            if asset.fiscal_depreciation_line_ids:
                book_value -= sum([depr.accelerated_value for depr in asset.fiscal_depreciation_line_ids], 0.0)
        return book_value

    def _get_regularization_tax_coeff(self, cr, uid, asset, context=None):
        regularization_tax_coeff = 0.0
        total_years = asset.accounting_periods * asset.period_length / 12
        if total_years and asset.sale_date[:4] < asset.depreciation_date_stop[:4] \
                and asset.purchase_tax_ids and not asset.sale_tax_ids:
            remaining_years = total_years - (int(asset.sale_date[:4]) - int(asset.depreciation_date_start[:4]) + 1)
            regularization_tax_coeff = float(remaining_years) / total_years
        return regularization_tax_coeff

    def get_sale_infos(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = {}
        for asset in self.browse(cr, uid, ids, context):
            book_value = self._get_book_value_at_disposal(cr, uid, asset, context)
            regularization_tax_amount = asset.purchase_tax_amount * self._get_regularization_tax_coeff(cr, uid, asset, context)
            sale_result = asset.sale_value - book_value - regularization_tax_amount
            accumulated_amortization_value = asset.purchase_value - book_value
            res[asset.id] = {
                'regularization_tax_amount': regularization_tax_amount,
                'sale_result': sale_result,
                'sale_result_short_term': min(sale_result, accumulated_amortization_value),
                'sale_result_long_term': sale_result > accumulated_amortization_value and sale_result - accumulated_amortization_value or 0.0,
                'book_value': book_value,
                'accumulated_amortization_value': accumulated_amortization_value,
            }
        return res

    def confirm_asset_sale(self, cr, uid, ids, context=None):
        self.compute_depreciation_board(cr, uid, ids, context)
        sale_infos_by_asset = self.get_sale_infos(cr, uid, ids, context)
        for asset_id in sale_infos_by_asset:
            self.write(cr, uid, asset_id, sale_infos_by_asset[asset_id], context)
        return self.write(cr, uid, ids, {'state': 'close'}, context)

    def button_confirm_asset_sale(self, cr, uid, ids, context=None):
        self.confirm_asset_sale(cr, uid, ids, context)
        return {'type': 'ir.actions.act_window_close'}

    def output(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'is_out': True}, context)

    def button_output(self, cr, uid, ids, context=None):
        return self.output(cr, uid, ids, context)

    def run_tests(self):
        "Call from module test/run_tests.yml"
        import run_tests
        run_tests.main()
