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

import logging

import decimal_precision as dp
from osv import orm, fields
from tools import float_round

_logger = logging.getLogger(__name__)


class AccountAssetSplitWizard(orm.TransientModel):
    _name = 'account.asset.split_wizard'
    _description = 'Asset Split Wizard'
    _rec_name = 'asset_id'

    _columns = {
        'asset_id': fields.many2one('account.asset.asset', 'Asset', required=True, ondelete='cascade'),
        'initial_purchase_value': fields.related('asset_id', 'purchase_value', type='float', digits_compute=dp.get_precision('Account'),
                                                 string='Gross Value', readonly=True),
        'initial_salvage_value': fields.related('asset_id', 'salvage_value', type='float', digits_compute=dp.get_precision('Account'),
                                                string='Salvage Value', readonly=True),
        'initial_quantity': fields.related('asset_id', 'quantity', type='float', string='Quantity', readonly=True),
        'purchase_value': fields.float('Gross Value', digits_compute=dp.get_precision('Account'), required=True),
        'salvage_value': fields.float('Salvage Value', digits_compute=dp.get_precision('Account'), required=True),
        'quantity': fields.float('Quantity', required=True),
    }

    def _check_split(self, cr, uid, ids, field, operator='>', context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for wizard in self.browse(cr, uid, ids, context):
            if eval('%s %s %s' % (getattr(wizard, field), operator, getattr(wizard.asset_id, field))) \
                    or getattr(wizard, field) < 0.0:
                return False
        return True

    def _check_purchase_value(self, cr, uid, ids, context=None):
        return self._check_split(cr, uid, ids, 'purchase_value', '>=', context)

    def _check_quantity(self, cr, uid, ids, context=None):
        return self._check_split(cr, uid, ids, 'quantity', context=context)

    def _check_salvage_value(self, cr, uid, ids, context=None):
        return self._check_split(cr, uid, ids, 'salvage_value', context=context)

    def _check_salvage_value2(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for asset in self.browse(cr, uid, ids, context):
            if asset.salvage_value < 0 or asset.salvage_value > asset.purchase_value:
                return False
        return True

    _constraints = [
        (_check_purchase_value, 'You must specify a gross value lower than the initial one!', ['purchase_value', 'initial_purchase_value']),
        (_check_quantity, 'You must specify a quantity lower than the initial one!', ['quantity', 'initial_quantity']),
        (_check_salvage_value, 'You must specify a salvage value lower than the initial one!', ['salvage_value', 'initial_salvage_value']),
        (_check_salvage_value2, 'Salvage value cannot be negative nor bigger than gross value!', ['salvage_value', 'purchase_value']),
    ]

    def onchange_asset_id(self, cr, uid, ids, asset_id, context=None):
        res = {'value': {}}
        if asset_id:
            res['value'] = self.pool.get('account.asset.asset').read(cr, uid, asset_id, ['purchase_value', 'quantity'], context)
            del res['value']['id']
        return res

    def _regularize_new_asset_depreciations(self, cr, uid, new_asset_id, context=None):
        new_asset = self.pool.get('account.asset.asset').browse(cr, uid, new_asset_id, context)
        line_to_update_ids = []
        for line in new_asset.depreciation_line_ids:
            if line.move_id:
                value_field = line.depreciation_type == 'fiscal' and 'accelerated_value' or 'depreciation_value'
                gap = line.move_id.amount - sum([getattr(l, value_field) for l in line.move_id.asset_depreciation_line_ids])
                rounding = line.asset_id.currency_id.rounding
                gap = float_round(gap, precision_digits=len(str(rounding).split('.')[-1]))
                if gap > rounding:
                    # TODO: fix me
                    _logger.warning('Asset Split [new_asset_id=%s,line_id=%s,depreciation_type=%s] - Gap = %s > %s'
                                    % (new_asset_id, line.id, line.depreciation_type, gap, rounding))
                if gap:
                    line.write({'depreciation_value': line.depreciation_value + gap})
                    line_to_update_ids.append(line.id)
        if line_to_update_ids:
            self.pool.get('account.asset.depreciation.line')._store_set_values(cr, uid, line_to_update_ids, ['accelerated_value'], context)

    def _link_to_account_moves(self, cr, uid, origin_asset_id, new_asset_id, move_ids_by_depreciation, context=None):
        for asset in self.pool.get('account.asset.asset').browse(cr, uid, [origin_asset_id, new_asset_id], context):
            for line in asset.depreciation_line_ids:
                key = (line.depreciation_type, line.depreciation_date)
                if key in move_ids_by_depreciation:
                    line.write({'move_id': move_ids_by_depreciation[key]})

    def _split_asset(self, cr, uid, origin_asset, vals, default, context=None):
        context = context or {}
        context['asset_split'] = True
        asset_obj = self.pool.get('account.asset.asset')
        depreciation_line_obj = self.pool.get('account.asset.depreciation.line')
        new_asset_id = asset_obj.copy(cr, uid, origin_asset.id, default, context)
        origin_asset.write(vals)
        move_ids_by_depreciation = dict([((line.depreciation_type, line.depreciation_date), line.move_id.id)
                                         for line in origin_asset.depreciation_line_ids if line.move_id
                                         and line.depreciation_type != 'exceptional'])
        line_ids = [line.id for line in origin_asset.accounting_depreciation_line_ids + origin_asset.fiscal_depreciation_line_ids]
        depreciation_line_obj.unlink(cr, uid, line_ids, context)
        asset_obj.compute_depreciation_board(cr, uid, origin_asset.id, context)
        if origin_asset.state != 'draft':
            asset_obj.confirm_asset_purchase(cr, uid, new_asset_id, context)
        if origin_asset.state == 'open':
            asset_obj.validate(cr, uid, new_asset_id, context)
        else:
            asset_obj.compute_depreciation_board(cr, uid, new_asset_id, context)
        self._link_to_account_moves(cr, uid, origin_asset.id, new_asset_id, move_ids_by_depreciation, context)
        self._regularize_new_asset_depreciations(cr, uid, new_asset_id, context)

    def button_validate(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for wizard in self.browse(cr, uid, ids, context):
            default = {'parent_id': wizard.asset_id.id, 'origin_id': wizard.asset_id.id,
                       'purchase_value': wizard.purchase_value, 'salvage_value': wizard.salvage_value}
            vals = {'purchase_value': wizard.asset_id.purchase_value - wizard.purchase_value,
                    'salvage_value': wizard.asset_id.salvage_value - wizard.salvage_value}
            if wizard.quantity != wizard.asset_id.quantity:
                default['quantity'] = wizard.quantity
                vals['quantity'] = wizard.asset_id.quantity - wizard.quantity
            self._split_asset(cr, uid, wizard.asset_id, vals, default, context)
        return {'type': 'ir.actions.act_window_close'}
