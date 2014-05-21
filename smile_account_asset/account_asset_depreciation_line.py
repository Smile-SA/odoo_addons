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

from account_asset import ASSET_STATES, ASSET_TYPES


class AccountAssetDepreciationLine(orm.Model):
    _name = 'account.asset.depreciation.line'
    _description = 'Asset depreciation line'
    _rec_name = 'depreciation_date'
    _order = 'asset_id, depreciation_type, depreciation_date'

    def __init__(self, pool, cr):
        super(AccountAssetDepreciationLine, self).__init__(pool, cr)
        cr.execute("SELECT * FROM pg_proc WHERE proname = 'last' AND proisagg;")
        if not cr.fetchall():
            cr.execute("""-- Create a function that always returns the last non-NULL item
CREATE OR REPLACE FUNCTION public.last_agg ( anyelement, anyelement )
RETURNS anyelement LANGUAGE sql IMMUTABLE STRICT AS $$
        SELECT $2;
$$;

-- And then wrap an aggregate around it
CREATE AGGREGATE public.last (
        sfunc    = public.last_agg,
        basetype = anyelement,
        stype    = anyelement
);""")

    def _get_asset_info(self, cr, uid, ids, name, args, context=None):
        res = {}
        category_obj = self.pool.get('account.asset.category')
        company_obj = self.pool.get('res.company')
        category_by_asset_id = {}
        fiscalyear_start_day_by_company_id = {}
        for line in self.browse(cr, uid, ids, context):
            asset = line.asset_id
            year = line.depreciation_date[:4]
            if asset.company_id.id not in fiscalyear_start_day_by_company_id:
                fiscalyear_start_day_by_company_id[asset.company_id.id] = company_obj.get_fiscalyear_start_day(cr, uid, asset.company_id.id, context)
            if line.depreciation_date[5:] < fiscalyear_start_day_by_company_id[asset.company_id.id]:
                year = str(int(line.depreciation_date[:4]) + 1)
            if asset.id not in category_by_asset_id:
                category_by_asset_id[asset.id] = category_obj.browse(cr, uid, asset.category_id.id, {'force_company': asset.company_id.id})
            category = category_by_asset_id[asset.id]
            if line.depreciation_type == 'accounting':
                account_id = category.accounting_depreciation_account_id.id
            if line.depreciation_type == 'fiscal':
                account_id = asset.company_id.fiscal_depreciation_account_id.id
            if line.depreciation_type == 'exceptional':
                account_id = category.exceptional_depreciation_account_id.id
            res[line.id] = {
                'purchase_value': asset.purchase_value,
                'salvage_value': asset.salvage_value,
                'category_id': asset.category_id.id,
                'currency_id': asset.currency_id.id,
                'company_id': asset.company_id.id,
                'state': asset.state,
                'asset_type': asset.asset_type,
                'benefit_accelerated_depreciation': asset.benefit_accelerated_depreciation,
                'account_id': account_id,
                'year': year,
                'is_posted': line.is_posted or bool(line.move_id),
            }
        return res

    def _get_fiscal_depreciation_info(self, cr, uid, ids, name, args, context=None):
        res = {}
        fields_to_read = ['depreciation_date', 'asset_id', 'depreciation_value', 'depreciation_type']
        lines = sorted(self.read(cr, uid, ids, fields_to_read, context, '_classic_write'), key=lambda d: d['depreciation_date'])
        line_ids = [line['id'] for line in lines]

        fiscal_lines = [line for line in lines if line['depreciation_type'] == 'fiscal']
        if fiscal_lines:
            depr_line_ids = self.search(cr, uid, [('asset_id', 'in', [line['asset_id'] for line in fiscal_lines]),
                                                  ('depreciation_type', '!=', 'exceptional')], context=context)
            depr_lines = self.read(cr, uid, depr_line_ids, fields_to_read, context, '_classic_write')
            accounting_lines_by_asset_and_date = {}
            max_depr_date_by_asset = {}
            accelerated_amount_by_asset = {}
            for line in depr_lines:
                if line['depreciation_type'] == 'accounting':
                    accounting_lines_by_asset_and_date.setdefault(line['asset_id'], {})[line['depreciation_date']] = line['depreciation_value']
                else:
                    if line['id'] not in line_ids:
                        accelerated_amount_by_asset.setdefault(line['asset_id'], 0.0)
                        accelerated_amount_by_asset[line['asset_id']] += line['depreciation_value']
                    if line['depreciation_date'] > max_depr_date_by_asset.get(line['asset_id'], ''):
                        max_depr_date_by_asset[line['asset_id']] = line['depreciation_date']

        for line in lines:
            accounting_value = accelerated_value = 0.0
            if line['depreciation_type'] == 'fiscal':
                accounting_value = accounting_lines_by_asset_and_date.get(line['asset_id'], {}).get(line['depreciation_date'], 0.0)
                accelerated_value = line['depreciation_value'] - accounting_value
                if line['depreciation_date'] == max_depr_date_by_asset[line['asset_id']]:
                    accelerated_value = -accelerated_amount_by_asset.get(line['asset_id'], 0.0)
                else:
                    accelerated_amount_by_asset.setdefault(line['asset_id'], 0.0)
                    accelerated_amount_by_asset[line['asset_id']] += accelerated_value
            res[line['id']] = {
                'accounting_value': accounting_value,
                'accelerated_value': accelerated_value,
            }
        return res

    def _get_line_ids_from_depreciation_lines(self, cr, uid, ids, context=None):
        res = []
        for line in self.browse(cr, uid, ids, context):
            if line.depreciation_type != 'exceptional':
                res.extend([l.id for l in line.asset_id.depreciation_line_ids if l.depreciation_type == 'fiscal' and not l.is_posted])
        return list(set(res))

    def _get_line_ids_from_assets(self, cr, uid, ids, context=None):
        return sum([asset['depreciation_line_ids'] for asset in self.read(cr, uid, ids, ['depreciation_line_ids'], context)], [])

    def _get_line_ids_from_asset_categories(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        cr.execute('SELECT id FROM account_asset_depreciation_line WHERE category_id IN %s', (tuple(ids),))
        return [line[0] for line in cr.fetchall()]

    def _get_line_ids_from_assets_for_account(self, cr, uid, ids, context=None):
        return self.pool.get('account.asset.depreciation.line').search(cr, uid, [('asset_id', 'in', ids)], context=context)

    def _get_line_ids_from_asset_categories_for_account(self, cr, uid, ids, context=None):
        return self.pool.get('account.asset.depreciation.line').search(cr, uid, [('category_id', 'in', ids)], context=context)

    def _get_line_ids_from_companies_for_account(self, cr, uid, ids, context=None):
        return self.pool.get('account.asset.depreciation.line').search(cr, uid, [('company_id', 'in', ids)], context=context)

    def _is_manual(self, cr, uid, ids, name, arg, context=None):
        # WARNING: method copied in AccountAssetAsset._update_or_create_depreciation_lines
        res = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        for line in self.browse(cr, uid, ids, context):
            res[line.id] = getattr(line.asset_id, '%s_method' % line.depreciation_type) == 'manual'
        return res

    def _set_is_posted(self, cr, uid, line_id, name, value, arg, context=None):
        cr.execute("UPDATE account_asset_depreciation_line SET is_posted = %s WHERE id = %s", (value, line_id))
        return True

    _columns = {
        'asset_id': fields.many2one('account.asset.asset', 'Asset', required=True, ondelete='cascade', select=True),
        'depreciation_type': fields.selection([('accounting', 'Accounting'), ('fiscal', 'Fiscal'), ('exceptional', 'Exceptional')], 'Type',
                                              required=True, select=True),
        'depreciation_date': fields.date('Date', required=True),
        'base_value': fields.float('Base Amount', digits_compute=dp.get_precision('Account'), readonly=True),
        'previous_years_accumulated_value': fields.float('Previous Years Accumulated Depreciation', digits_compute=dp.get_precision('Account'),
                                                         readonly=True, group_operator="last"),
        'current_year_accumulated_value': fields.float('Current Year Accumulated Depreciation', digits_compute=dp.get_precision('Account'),
                                                       readonly=True, group_operator="last"),
        'depreciation_value': fields.float('Depreciation', digits_compute=dp.get_precision('Account')),
        'accumulated_value': fields.float('Accumulated Depreciation', digits_compute=dp.get_precision('Account'), readonly=True),
        'exceptional_value': fields.float('Exceptional Depreciation', digits_compute=dp.get_precision('Account'), readonly=True),
        'book_value': fields.float('Book value', digits_compute=dp.get_precision('Account'), readonly=True),
        'book_value_wo_exceptional': fields.float('Book value at end without exceptional', digits_compute=dp.get_precision('Account'),
                                                  readonly=True),
        'move_id': fields.many2one('account.move', 'Depreciation Entry', ondelete='restrict'),
        'accounting_value': fields.function(_get_fiscal_depreciation_info, method=True, type='float',
                                            digits_compute=dp.get_precision('Account'), store={
                                                'account.asset.depreciation.line': (_get_line_ids_from_depreciation_lines, None, 5),
                                            }, string='Accounting Depreciation', multi='fiscal_depreciation'),
        'accelerated_value': fields.function(_get_fiscal_depreciation_info, method=True, type='float',
                                             digits_compute=dp.get_precision('Account'), store={
                                                 'account.asset.depreciation.line': (_get_line_ids_from_depreciation_lines, None, 5),
                                             }, string='Accelerated Depreciation', multi='fiscal_depreciation'),
        'purchase_value': fields.function(_get_asset_info, method=True, type='float', digits_compute=dp.get_precision('Account'), store={
            'account.asset.depreciation.line': (lambda self, cr, uid, ids, context=None: ids, ['asset_id'], 5),
            'account.asset.asset': (_get_line_ids_from_assets, ['purchase_value'], 5),
        }, string="Gross Value", multi="asset_info"),
        'salvage_value': fields.function(_get_asset_info, method=True, type='float', digits_compute=dp.get_precision('Account'), store={
            'account.asset.depreciation.line': (lambda self, cr, uid, ids, context=None: ids, ['asset_id'], 5),
            'account.asset.asset': (_get_line_ids_from_assets, ['salvage_value'], 5),
        }, string="Salvage Value", multi="asset_info"),
        'category_id': fields.function(_get_asset_info, method=True, type='many2one', relation='account.asset.category', store={
            'account.asset.depreciation.line': (lambda self, cr, uid, ids, context=None: ids, ['asset_id'], 5),
            'account.asset.asset': (_get_line_ids_from_assets, ['category_id'], 5),
        }, string="Asset Category", ondelete='restrict', multi="asset_info"),
        'company_id': fields.function(_get_asset_info, method=True, type='many2one', relation='res.company', string="Company", store={
            'account.asset.depreciation.line': (lambda self, cr, uid, ids, context=None: ids, ['asset_id'], 5),
            'account.asset.asset': (_get_line_ids_from_assets, ['category_id'], 5),
        }, ondelete='restrict', multi="asset_info"),
        'currency_id': fields.function(_get_asset_info, method=True, type="many2one", relation="res.currency", string="Currency", store={
            'account.asset.depreciation.line': (lambda self, cr, uid, ids, context=None: ids, ['asset_id'], 5),
            'account.asset.asset': (_get_line_ids_from_assets, ['company_id'], 5),
        }, ondelete='restrict', multi="asset_info"),
        'state': fields.function(_get_asset_info, method=True, type='selection', selection=ASSET_STATES, string="State", store={
            'account.asset.depreciation.line': (lambda self, cr, uid, ids, context=None: ids, ['asset_id'], 5),
            'account.asset.asset': (_get_line_ids_from_assets, ['state'], 5),
        }, multi="asset_info"),
        'asset_type': fields.function(_get_asset_info, method=True, type='selection', selection=ASSET_TYPES, string="Type", store={
            'account.asset.depreciation.line': (lambda self, cr, uid, ids, context=None: ids, ['asset_id'], 5),
            'account.asset.asset': (_get_line_ids_from_assets, ['asset_type'], 5),
        }, ondelete='restrict', multi="asset_info"),

        'benefit_accelerated_depreciation': fields.function(_get_asset_info, method=True, type='boolean', store={
            'account.asset.depreciation.line': (lambda self, cr, uid, ids, context=None: ids, ['asset_id'], 5),
            'account.asset.asset': (_get_line_ids_from_assets, ['purchase_value', 'salvage_value', 'accounting_method', 'accounting_annuities',
                                                                'accounting_rate', 'fiscal_method', 'fiscal_annuities', 'fiscal_rate'], 5),
        }, string="Benefit accelerated depreciation", multi="asset_info"),
        'year': fields.function(_get_asset_info, method=True, type='char', size=4, string='Year', store={
            'account.asset.depreciation.line': (lambda self, cr, uid, ids, context=None: ids, ['depreciation_date'], 5),
        }, multi="asset_info"),
        'account_id': fields.function(_get_asset_info, method=True, type='many2one', relation="account.account", store={
            'account.asset.depreciation.line': (lambda self, cr, uid, ids, context=None: ids, ['asset_id'], 5),
            'account.asset.asset': (_get_line_ids_from_assets_for_account, ['category_id'], 5),
            'account.asset.category': (_get_line_ids_from_asset_categories_for_account, ['accounting_depreciation_account_id',
                                                                                         'exceptional_depreciation_account_id'], 5),
            'res.company': (_get_line_ids_from_companies_for_account, ['fiscal_depreciation_account_id'], 5),
        }, string="Account", multi="asset_info"),
        'is_posted': fields.function(_get_asset_info, fnct_inv=_set_is_posted, method=True, type='boolean', string='Posted Depreciation', store={
            'account.asset.depreciation.line': (lambda self, cr, uid, ids, context=None: ids, ['move_id'], 5),
        }, multi="asset_info", readonly=True, select=True),
        'is_manual': fields.function(_is_manual, method=True, type='boolean', string='Manual Depreciation'),
    }

    _defaults = {
        'depreciation_date': lambda * a: time.strftime('%Y-%m-%d'),
        'depreciation_type': 'exceptional',
    }

    def check_constraints(self, cr, uid, ids, context=None):
        # _constraints are too slow
        if isinstance(ids, (int, long)):
            ids = [ids]
        for line in self.browse(cr, uid, ids, context):
            if line.depreciation_date < line.asset_id.purchase_date:
                raise orm.except_orm(_('Error'),
                                     _('Depreciation date must be after purchase date! [Reference=%s,DepreciationDate=%s,PurchaseDate=%s]')
                                     % (line.asset_id.code, line.depreciation_date, line.asset_id.purchase_date))
            if line.depreciation_type == 'exceptional':
                cr.execute("SELECT id FROM account_period WHERE state='draft' AND date_start <= %s AND date_stop >= %s AND company_id = %s",
                           (line.depreciation_date, line.depreciation_date, line.company_id.id))
                res = cr.fetchall()
                if not res:
                    raise orm.except_orm(_('Error'), _('Depreciation date must be in current fiscal year!'))
            if line.depreciation_value > line.asset_id.purchase_value:
                raise orm.except_orm(_('Error'), _('Depreciation value cannot be bigger than gross value!'))
            if line.book_value > line.book_value_wo_exceptional:
                raise orm.except_orm(_('Error'), _('Book value with exceptional depreciations cannot be superior to book value '
                                                   'without exceptional depreciations, nor inferior to salvage value!'))
        return True

    def create(self, cr, uid, vals, context=None):
        context_copy = context and context.copy() or {}
        context_copy['no_validate'] = True
        res_id = super(AccountAssetDepreciationLine, self).create(cr, uid, vals, context_copy)
        self._validate(cr, uid, [res_id], context)
        return res_id

    def _validate(self, cr, uid, ids, context=None):
        context = context or {}
        if context.get('no_validate'):
            return
        super(AccountAssetDepreciationLine, self)._validate(cr, uid, ids, context)
        self.check_constraints(cr, uid, ids, context)

    def validate_exceptional_depreciation(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        asset_ids = [line.asset_id.id for line in self.browse(cr, uid, ids, context)]
        return self.pool.get('account.asset.asset').compute_depreciation_board(cr, uid, asset_ids, context)

    def button_validate_exceptional_depreciation(self, cr, uid, ids, context=None):
        self.validate_exceptional_depreciation(cr, uid, ids, context)
        return {'type': 'ir.actions.act_window_close'}

    def _search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False, access_rights_uid=None):
        context = context or {}
        if context.get('search_in_current_month'):
            date_start = datetime.today().strftime('%Y-%m-01')
            date_stop = (datetime.strptime(date_start, '%Y-%m-%d') + relativedelta(months=1)).strftime('%Y-%m-%d')
            domain = ['&', ('depreciation_date', '>=', date_start), ('depreciation_date', '<', date_stop)]
            args = args and (['&'] + domain + args) or domain
        if context.get('search_in_three_month'):
            date_stop = datetime.today().strftime('%Y-%m-01')
            date_start = (datetime.strptime(date_stop, '%Y-%m-%d') - relativedelta(months=3)).strftime('%Y-%m-%d')
            domain = ['&', ('depreciation_date', '>=', date_start), ('depreciation_date', '<', date_stop)]
            args = args and (['&'] + domain + args) or domain
        return super(AccountAssetDepreciationLine, self)._search(cr, uid, args, offset, limit, order, context, count, access_rights_uid)
