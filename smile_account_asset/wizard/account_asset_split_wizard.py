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


class AccountAssetSplitWizard(orm.TransientModel):
    _name = 'account.asset.split_wizard'
    _description = 'Asset Split Wizard'

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

    def button_validate(self, cr, uid, ids, context=None):
        asset_obj = self.pool.get('account.asset.asset')
        if isinstance(ids, (int, long)):
            ids = [ids]
        for wizard in self.browse(cr, uid, ids, context):
            default = {'parent_id': wizard.asset_id.id, 'purchase_value': wizard.purchase_value, 'salvage_value': wizard.salvage_value}
            vals = {'purchase_value': wizard.asset_id.purchase_value - wizard.purchase_value,
                    'salvage_value': wizard.asset_id.salvage_value - wizard.salvage_value}
            if wizard.quantity != wizard.asset_id.quantity:
                default['quantity'] = wizard.quantity
                vals['quantity'] = wizard.asset_id.quantity - wizard.quantity
            new_asset_id = asset_obj.copy(cr, uid, wizard.asset_id.id, default, context)
            wizard.asset_id.write(vals)
            if wizard.asset_id.state == 'open':
                move_ids = {}
                move_ids['accounting'] = dict([(line.depreciation_date, line.move_id.id)
                                               for line in wizard.asset_id.accounting_depreciation_line_ids])
                move_ids['fiscal'] = dict([(line.depreciation_date, line.move_id.id)
                                           for line in wizard.asset_id.fiscal_depreciation_line_ids])
                line_ids = [line.id for line in wizard.asset_id.accounting_depreciation_line_ids + wizard.asset_id.fiscal_depreciation_line_ids]
                self.pool.get('account.asset.depreciation.line').unlink(cr, uid, line_ids, context)
                asset_obj.compute_depreciation_board(cr, uid, wizard.asset_id.id, context)
                asset_obj.validate(cr, uid, new_asset_id, context)
                for asset_id in (wizard.asset_id.id, new_asset_id):
                    asset = asset_obj.browse(cr, uid, asset_id, context)
                    for line in asset.accounting_depreciation_line_ids + asset.fiscal_depreciation_line_ids:
                        if move_ids[line.depreciation_type].get(line.depreciation_date, False):
                            line.write({'move_id': move_ids[line.depreciation_type][line.depreciation_date]})
            else:
                asset_obj.compute_depreciation_board(cr, uid, wizard.asset_id.id, context)
                asset_obj.compute_depreciation_board(cr, uid, new_asset_id, context)
        return {'type': 'ir.actions.act_window_close'}
