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

import time

import decimal_precision as dp
from osv import orm, fields

from account_asset import ASSET_STATES, ASSET_TYPES


class AccountAssetDepreciationLine(orm.Model):
    _name = 'account.asset.depreciation.line'
    _description = 'Asset depreciation line'
    _rec_name = 'date'
    _order = 'asset_id, depreciation_type, depreciation_date'

    def _get_fiscal_depreciation_info(self, cr, uid, ids, name, args, context=None):
        res = {}
        lines = self.read(cr, uid, ids, ['depreciation_date', 'asset_id', 'depreciation_value', 'depreciation_type'], context, '_classic_write')

        fiscal_lines = [line for line in lines if line['depreciation_type'] == 'fiscal']
        accounting_line_ids = self.search(cr, uid, [('asset_id', 'in', [line['asset_id'] for line in fiscal_lines]),
                                                    ('depreciation_type', '=', 'accounting')], context=context)
        accounting_lines = self.read(cr, uid, accounting_line_ids, ['depreciation_date', 'asset_id', 'depreciation_value'], context, '_classic_write')
        accounting_lines_by_asset_and_date = {}
        for line in accounting_lines:
            accounting_lines_by_asset_and_date.setdefault(line['asset_id'], {})[line['depreciation_date']] = line['depreciation_value']

        for line in lines:
            res[line['id']] = {
                'accounting_value': accounting_lines_by_asset_and_date.get(line['asset_id'], {}).get(line['depreciation_date'], 0.0),
                'accelerated_value': line['depreciation_value']
                - accounting_lines_by_asset_and_date.get(line['asset_id'], {}).get(line['depreciation_date'], 0.0),
            }
        return res

    def _get_account_id(self, cr, uid, ids, name, args, context=None):
        res = {}.fromkeys(ids, False)
        for line in self.browse(cr, uid, ids, context):
            asset = line.asset_id
            if line.depreciation_type == 'accounting':
                res[line.id] = asset.category_id.amortization_account_id.id
            if line.depreciation_type == 'fiscal':
                res[line.id] = asset.company_id.fiscal_depreciation_account_id.id
            if line.depreciation_type == 'exceptional':
                res[line.id] = asset.category_id.depreciation_account_id.id
        return res

    def _get_year(self, cr, uid, ids, name, args, context=None):
        res = {}
        company_obj = self.pool.get('res.company')
        fiscalyear_start_day_by_company_id = {}
        for line in self.browse(cr, uid, ids, context):
            company_id = line.asset_id.company_id.id
            fiscalyear_start_day = fiscalyear_start_day_by_company_id.get(company_id)
            if not fiscalyear_start_day:
                fiscalyear_start_day_by_company_id[company_id] = company_obj.get_fiscalyear_start_day(cr, uid, company_id, context)
            if line.depreciation_date[5:] < fiscalyear_start_day:
                year = str(int(line.depreciation_date[:4]) + 1)
            else:
                year = line.depreciation_date[:4]
            res[line.id] = year
        return res

    def _get_line_ids_from_depreciation_lines(self, cr, uid, ids, context=None):
        res = []
        for line in self.browse(cr, uid, ids, context):
            if line.depreciation_type != 'exceptional':
                res.extend([l.id for l in line.asset_id.depreciation_line_ids if l.depreciation_type == 'fiscal'])
        return list(set(res))

    def _get_line_ids_from_assets(self, cr, uid, ids, context=None):
        return sum([asset['depreciation_line_ids'] for asset in self.read(cr, uid, ids, ['depreciation_line_ids'], context)], [])

    def _get_line_ids_from_asset_categories(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        cr.execute('SELECT id FROM account_asset_depreciation_line WHERE category_id IN %s', (tuple(ids),))
        return [line[0] for line in cr.fetchall()]

    def _get_line_ids_from_companies(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        cr.execute('SELECT id FROM account_asset_depreciation_line WHERE company_id IN %s', (tuple(ids),))
        return [line[0] for line in cr.fetchall()]

    def _is_manual(self, cr, uid, ids, name, arg, context=None):
        res = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        for line in self.browse(cr, uid, ids, context):
            res[line.id] = getattr(line.asset_id, '%s_method' % line.depreciation_type) == 'manual'
        return res

    _columns = {
        'asset_id': fields.many2one('account.asset.asset', 'Asset', required=True, ondelete='cascade'),
        'depreciation_type': fields.selection([('accounting', 'Accounting'), ('fiscal', 'Fiscal'), ('exceptional', 'Exceptional')], 'Type',
                                              required=True, select=True),
        'depreciation_date': fields.date('Date', required=True),
        'base_value': fields.float('Base Amount', digits_compute=dp.get_precision('Account'), readonly=True),
        'previous_accumulated_value': fields.float('Previous Accumulated Depreciation', digits_compute=dp.get_precision('Account'), readonly=True),
        'depreciation_value': fields.float('Depreciation', digits_compute=dp.get_precision('Account')),
        'accumulated_value': fields.float('Accumulated Depreciation', digits_compute=dp.get_precision('Account'), readonly=True),
        'exceptional_value': fields.float('Exceptional Depreciation', digits_compute=dp.get_precision('Account'), readonly=True),
        'book_value': fields.float('Book value at end', digits_compute=dp.get_precision('Account'), readonly=True),
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
        'purchase_value': fields.related('asset_id', 'purchase_value', type='float', digits_compute=dp.get_precision('Account'), store={
            'account.asset.asset': (_get_line_ids_from_assets, ['purchase_value'], 5),
        }, string="Gross Value", readonly=True),
        'salvage_value': fields.related('asset_id', 'salvage_value', type='float', digits_compute=dp.get_precision('Account'), store={
            'account.asset.asset': (_get_line_ids_from_assets, ['salvage_value'], 5),
        }, string="Salvage Value", readonly=True),
        'category_id': fields.related('asset_id', 'category_id', type='many2one', relation='account.asset.category', string="Asset Category", store={
            'account.asset.asset': (_get_line_ids_from_assets, ['category_id'], 5),
        }, readonly=True, ondelete='restrict'),
        'account_id': fields.function(_get_account_id, method=True, type='many2one', relation="account.account", store={
            'account.asset.asset': (_get_line_ids_from_assets, ['category_id'], 5),
            'account.asset.category': (_get_line_ids_from_asset_categories, ['amortization_account_id', 'depreciation_account_id'], 5),
            'res.company': (_get_line_ids_from_companies, ['fiscal_depreciation_account_id'], 5),
        }, string="Account"),
        'company_id': fields.related('asset_id', 'company_id', type='many2one', relation='res.company', string="Company", store={
            'account.asset.asset': (_get_line_ids_from_assets, ['company_id'], 5),
        }, readonly=True, ondelete='restrict'),
        'currency_id': fields.related('asset_id', 'company_id', 'currency_id', type="many2one", relation="res.currency", string="Currency", store={
            'account.asset.asset': (_get_line_ids_from_assets, ['company_id'], 5),
        }, readonly=True, ondelete='restrict'),
        'state': fields.related('asset_id', 'state', type='selection', selection=ASSET_STATES, string="State", store={
            'account.asset.asset': (_get_line_ids_from_assets, ['state'], 5),
        }, readonly=True),
        'asset_type': fields.related('asset_id', 'asset_type', type='selection', selection=ASSET_TYPES, string="Type", store={
            'account.asset.asset': (_get_line_ids_from_assets, ['asset_type'], 5),
        }, readonly=True, ondelete='restrict'),
        'year': fields.function(_get_year, method=True, type='char', size=4, string='Year', store=True),
        'is_manual': fields.function(_is_manual, method=True, type='boolean', string='Manual Depreciation'),
    }

    _defaults = {
        'depreciation_date': lambda *a: time.strftime('%Y-%m-%d'),
        'depreciation_type': 'exceptional',
    }

    def _check_date(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for line in self.browse(cr, uid, ids, context):
            if line.depreciation_type == 'exceptional' \
                    and (line.depreciation_date < line.asset_id.depreciation_date_start
                         or line.depreciation_date > line.asset_id.depreciation_date_stop):
                return False
        return True

    def _check_date_for_exceptional(self, cr, uid, ids, context=None):
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context).company_id.id
        if isinstance(ids, (int, long)):
            ids = [ids]
        for line in self.browse(cr, uid, ids, context):
            if line.depreciation_type != 'exceptional':
                continue
            cr.execute("SELECT id FROM account_period WHERE state='draft' AND date_start <= %s AND date_stop >= %s AND company_id = %s",
                       (line.depreciation_date, line.depreciation_date, line.company_id.id or company_id))
            res = cr.fetchall()
            if not res:
                return False
        return True

    def _check_depreciation_value(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for line in self.browse(cr, uid, ids, context):
            if line.depreciation_value > line.asset_id.purchase_value:
                return False
        return True

    def _check_depreciation_value2(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for line in self.browse(cr, uid, ids, context):
            if not line.depreciation_value:
                return False
        return True

    def _check_book_value(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for line in self.browse(cr, uid, ids, context):
            if line.book_value > line.book_value_wo_exceptional:
                return False
        return True

    _constraints = [
        (_check_date, 'Depreciation date must be in depreciations board!', ['depreciation_date']),
        (_check_date_for_exceptional, 'Depreciation date must be in current fiscal year!', ['depreciation_date']),
        (_check_depreciation_value, 'Depreciation value cannot be bigger than gross value!', ['depreciation_value']),
        (_check_book_value, 'Book value with exceptional depreciations cannot be superior to book value without exceptional depreciations, '
                            'nor inferior to salvage value!',
            ['book_value', 'book_value_wo_exceptional']),
    ]

    def create(self, cr, uid, vals, context=None):
        depreciation_line_id = super(AccountAssetDepreciationLine, self).create(cr, uid, vals, context)
        fields_to_compute = [field for field in self._columns if isinstance(self._columns[field], (fields.function, fields.related))
                             and self._columns[field].store]
        self._store_set_values(cr, uid, [depreciation_line_id], fields_to_compute, context)
        return depreciation_line_id

    def validate_exceptional_depreciation(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        asset_ids = [line.asset_id.id for line in self.browse(cr, uid, ids, context)]
        return self.pool.get('account.asset.asset').compute_depreciation_board(cr, uid, asset_ids, context)

    def button_validate_exceptional_depreciation(self, cr, uid, ids, context=None):
        self.validate_exceptional_depreciation(cr, uid, ids, context)
        return {'type': 'ir.actions.act_window_close'}
