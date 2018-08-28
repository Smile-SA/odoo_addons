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

from account_asset_category import _get_rates_visibility, _get_res_ids_from_depreciation_methods


class AccountAssetHistory(orm.Model):
    _name = 'account.asset.history'
    _description = 'Asset history'
    _rec_name = 'asset_id'
    _order = 'create_date desc'

    def _get_accounting_methods(self, cr, uid, context=None):
        return self.pool.get('account.asset.depreciation.method').get_methods_selection(cr, uid, 'accounting', context)

    def _get_fiscal_methods(self, cr, uid, context=None):
        return self.pool.get('account.asset.depreciation.method').get_methods_selection(cr, uid, 'fiscal', context)

    def _get_rates_visibility(self, cr, uid, ids, name, arg, context=None):
        return _get_rates_visibility(self, cr, uid, ids, name, arg, context=None)

    def _get_history_ids_from_depreciation_methods(self, cr, uid, ids, context=None):
        return _get_res_ids_from_depreciation_methods(self, self.pool.get('account.asset.history'), cr, uid, ids, context)

    _columns = {
        'create_date': fields.datetime('Until', readonly=True),
        'user_id': fields.many2one('res.users', 'User', readonly=True, ondelete='restrict'),
        'asset_id': fields.many2one('account.asset.asset', 'Asset', required=True, ondelete='cascade'),
        'category_id': fields.many2one('account.asset.category', 'Asset Category', required=True, ondelete='restrict'),
        'purchase_value': fields.float('Gross Value', digits_compute=dp.get_precision('Account'), required=True),
        'salvage_value': fields.float('Salvage Value', digits_compute=dp.get_precision('Account')),
        'purchase_date': fields.date('Purchase Date', required=True, readonly=True),
        'in_service_date': fields.date('In-service Date'),
        'accounting_method': fields.selection(_get_accounting_methods, 'Accounting Computation Method', required=True),
        'accounting_annuities': fields.integer('Accounting Annuities', required=False),
        'accounting_rate': fields.float('Accounting Amortization Rate (%)', digits=(4, 2)),
        'accounting_rate_visibility': fields.function(_get_rates_visibility, method=True, type='boolean', store={
            'account.asset.history': (lambda self, cr, uid, ids, context=None: ids, ['accounting_method'], 5),
            'account.asset.depreciation.method': (_get_history_ids_from_depreciation_methods, ['use_manual_rate'], 5),
        }, string='Amortization Rate Visibility', multi='rates_visibility'),
        'fiscal_method': fields.selection(_get_fiscal_methods, 'Fiscal Computation Method', required=True),
        'fiscal_annuities': fields.integer('Fiscal Annuities', required=False),
        'fiscal_rate': fields.float('Fiscal Amortization Rate (%)', digits=(4, 2)),
        'fiscal_rate_visibility': fields.function(_get_rates_visibility, method=True, type='boolean', store={
            'account.asset.history': (lambda self, cr, uid, ids, context=None: ids, ['fiscal_method'], 5),
            'account.asset.depreciation.method': (_get_history_ids_from_depreciation_methods, ['use_manual_rate'], 5),
        }, string='Amortization Rate Visibility', multi='rates_visibility'),
        'benefit_accelerated_depreciation': fields.boolean('Benefit Accelerated Depreciation', readonly=True),
        'note': fields.text('Reason', required=False),
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context=None: uid,
    }

    def _get_fields_to_read(self):
        fields_to_read = self._columns.keys()
        for field in ('create_date', 'user_id', 'asset_id', 'note'):
            fields_to_read.remove(field)
        return fields_to_read

    def onchange_depreciation_params(self, cr, uid, ids, purchase_value, salvage_value, purchase_date, in_service_date,
                                     accounting_method, accounting_annuities, accounting_rate,
                                     fiscal_method, fiscal_annuities, fiscal_rate, context=None):
        return self.pool.get('account.asset.asset').onchange_depreciation_params(cr, uid, ids, purchase_value, salvage_value,
                                                                                 purchase_date, in_service_date,
                                                                                 accounting_method, accounting_annuities, accounting_rate,
                                                                                 fiscal_method, fiscal_annuities, fiscal_rate, context)

    def onchange_asset_id(self, cr, uid, ids, asset_id, context=None):
        res = {'value': {}}
        if asset_id:
            res['value'] = self.pool.get('account.asset.asset').read(cr, uid, asset_id, self._get_fields_to_read(), context, '_classic_write')
            del res['value']['id']
        return res

    def onchange_category_id(self, cr, uid, ids, category_id, asset_id, context=None):
        if category_id == self.pool.get('account.asset.asset').read(cr, uid, asset_id, ['category_id'], context, '_classic_write')['category_id']:
            return self.onchange_asset_id(cr, uid, ids, asset_id, context)
        return self.pool.get('account.asset.asset').onchange_category_id(cr, uid, ids, category_id, context)

    def _get_values(self, cr, uid, vals, context=None):
        old_vals = vals.copy()
        old_vals.update(self.pool.get('account.asset.asset').read(cr, uid, vals['asset_id'], self._get_fields_to_read(), context, '_classic_write'))
        del old_vals['id']
        new_vals = dict([(field, vals[field]) for field in self._get_fields_to_read() if field in vals])
        for method_type in ('accounting', 'fiscal'):
            if vals.get('%s_method' % method_type) == 'none':
                old_vals['%s_annuities' % method_type] = 0
                old_vals['%s_rate' % method_type] = 0.0
        return old_vals, new_vals

    def create(self, cr, uid, vals, context=None):
        old_vals, new_vals = self._get_values(cr, uid, vals, context)
        asset_obj = self.pool.get('account.asset.asset')
        asset_obj.write(cr, uid, vals['asset_id'], new_vals, context)
        asset_obj.compute_depreciation_board(cr, uid, vals['asset_id'], context)
        return super(AccountAssetHistory, self).create(cr, uid, old_vals, context)

    def validate(self, cr, uid, ids, context=None):
        context = context or {}
        if context.get('asset_validation'):
            asset_id = self.browse(cr, uid, ids[0], context).asset_id.id
            self.pool.get('account.asset.asset').validate(cr, uid, asset_id, context)
        return True

    def button_validate(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'ids must be a list with only one item!'
        self.validate(cr, uid, ids, context)
        return {'type': 'ir.actions.act_window_close'}
