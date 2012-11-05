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

from account_asset import DEPRECIATION_METHODS


class AccountAssetHistory(orm.Model):
    _name = 'account.asset.history'
    _description = 'Asset history'
    _rec_name = 'asset_id'
    _order = 'create_date desc'

    _columns = {
        'create_date': fields.datetime('Until', readonly=True),
        'user_id': fields.many2one('res.users', 'User', readonly=True, ondelete='restrict'),
        'asset_id': fields.many2one('account.asset.asset', 'Asset', required=True, ondelete='cascade'),
        'purchase_value': fields.float('Gross Value', digits_compute=dp.get_precision('Account'), required=True),
        'salvage_value': fields.float('Salvage Value', digits_compute=dp.get_precision('Account')),
        'accounting_method': fields.selection(DEPRECIATION_METHODS, 'Accounting Computation Method', required=True),
        'accounting_periods': fields.integer('Number of Depreciations', required=False),
        'period_length': fields.integer('Period Length (in months)', required=False),
        'accounting_degressive_rate': fields.float('Accounting Degressive Rate (%)', digits=(4, 2)),
        'accounting_prorata': fields.boolean('Accounting Prorata Temporis', help='Indicates that the first depreciation entry for this '
                                             'asset have to be done from the purchase date instead of the first day of month'),
        'fiscal_method': fields.selection(DEPRECIATION_METHODS, 'Fiscal Computation Method', required=True),
        'fiscal_periods': fields.integer('Number of Depreciations', required=False),
        'fiscal_degressive_rate': fields.float('Fiscal Degressive Rate (%)', digits=(4, 2)),
        'fiscal_prorata': fields.boolean('Fiscal Prorata Temporis'),
        'note': fields.text('Reason', required=True),
    }

    _defaults = {
        'user_id': lambda self, cr, uid, context = None: uid,
    }

    def _get_fields_to_read(self):
        fields_to_read = self._columns.keys()
        for field in ('create_date', 'user_id', 'asset_id', 'note'):
            fields_to_read.remove(field)
        return fields_to_read

    def onchange_accounting_method(self, cr, uid, ids, accounting_method, context=None):
        res = {'value': {}}
        if accounting_method == 'none':
            res['value']['fiscal_method'] = 'none'
        return res

    def onchange_asset_id(self, cr, uid, ids, asset_id, context=None):
        res = {'value': {}}
        if asset_id:
            res['value'] = self.pool.get('account.asset.asset').read(cr, uid, asset_id, self._get_fields_to_read(), context, '_classic_write')
            del res['value']['id']
        return res

    def create(self, cr, uid, vals, context=None):
        asset_obj = self.pool.get('account.asset.asset')
        old_vals = vals.copy()
        old_vals.update(asset_obj.read(cr, uid, vals['asset_id'], self._get_fields_to_read(), context, '_classic_write'))
        del old_vals['id']
        new_vals = dict([(field, vals[field]) for field in self._get_fields_to_read() if field in vals])
        asset_obj.write(cr, uid, vals['asset_id'], new_vals, context)
        asset_obj.compute_depreciation_board(cr, uid, vals['asset_id'], context)
        return super(AccountAssetHistory, self).create(cr, uid, old_vals, context)

    def button_validate(self, cr, uid, ids, context=None):
        return {'type': 'ir.actions.act_window_close'}
