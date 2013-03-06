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
from tools.translate import _


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

    def _link_to_account_moves(self, cr, uid, old_asset, new_asset, move_infos, context=None):
        if not (move_infos['accounting'] or move_infos['fiscal']):
            return
        asset_obj = self.pool.get('account.asset.asset')
        old_asset = asset_obj.browse(cr, uid, old_asset.id, context)
        for line in old_asset.accounting_depreciation_line_ids + old_asset.fiscal_depreciation_line_ids:
            if move_infos[line.depreciation_type].get(line.depreciation_date):
                line.write({'move_id': move_infos[line.depreciation_type][line.depreciation_date]})
        new_asset.compute_depreciation_board()
        new_asset = asset_obj.browse(cr, uid, new_asset.id, context)
        old_vals = {}
        new_vals = {}
        computation_context = {}
        if new_asset.accounting_method not in ('none', 'manual'):
            old_vals['accounting_method'] = new_asset.accounting_method
            new_vals['accounting_method'] = 'manual'
            computation_context['depreciate_accounting_base_value'] = new_asset.accounting_method == 'degressive'
        if new_asset.fiscal_method != 'none':
            old_vals['fiscal_method'] = new_asset.fiscal_method
            new_vals['fiscal_method'] = 'manual'
            computation_context['depreciate_fiscal_base_value'] = new_asset.fiscal_method == 'degressive'
        if new_vals:
            new_asset.write(new_vals)
        move_obj = self.pool.get('account.move')
        for depreciation_type in move_infos:
            for depreciation_date, move_id in move_infos[depreciation_type].iteritems():
                for line in getattr(new_asset, '%s_depreciation_line_ids' % depreciation_type):
                    if line.depreciation_date == depreciation_date:
                        move = move_obj.browse(cr, uid, move_id, context)
                        amount_field = line.depreciation_type == 'fiscal' and 'accelerated_value' or 'depreciation_value'
                        depreciation_value = move.amount - abs(sum([getattr(dline, amount_field)
                                                                    for dline in move.asset_depreciation_line_ids]))
                        if line.depreciation_type == 'fiscal':
                            depreciation_value += line.accounting_value
                        line.write({'depreciation_value': depreciation_value})
        asset_obj.compute_depreciation_board(cr, uid, new_asset.id, computation_context)
        new_asset = asset_obj.browse(cr, uid, new_asset.id, context)
        for line in new_asset.accounting_depreciation_line_ids + new_asset.fiscal_depreciation_line_ids:
            if move_infos[line.depreciation_type].get(line.depreciation_date):
                line.write({'move_id': move_infos[line.depreciation_type][line.depreciation_date]})
        if old_vals:
            new_asset.write(old_vals)

    def _compute_depreciation_board(self, cr, uid, old_asset, new_asset, context=None):
        if old_asset.state == 'open':
            move_infos = {}
            move_infos['accounting'] = dict([(line.depreciation_date, line.move_id.id)
                                           for line in old_asset.accounting_depreciation_line_ids if line.move_id])
            move_infos['fiscal'] = dict([(line.depreciation_date, line.move_id.id)
                                       for line in old_asset.fiscal_depreciation_line_ids if line.move_id])
            line_ids = [line.id for line in old_asset.accounting_depreciation_line_ids + old_asset.fiscal_depreciation_line_ids]
            self.pool.get('account.asset.depreciation.line').unlink(cr, uid, line_ids, context)
            old_asset.compute_depreciation_board()
            self._link_to_account_moves(cr, uid, old_asset, new_asset, move_infos, context)
            new_asset.validate()
        else:
            old_asset.compute_depreciation_board()
            new_asset.compute_depreciation_board()
        return True

    def _regularize_account_moves(self, cr, uid, old_asset, new_asset, context=None):
        if old_asset.state == 'draft':
            return True
        context_copy = (context or {}).copy()
        context_copy['company_id'] = new_asset.company_id.id
        today = time.strftime('%Y-%m-%d')
        period_ids = self.pool.get('account.period').find(cr, uid, today, context_copy)
        vals = {
            'name': _('Asset Splitting: %s') % new_asset.name,
            'ref': new_asset.code,
            'date': today,
            'period_id': period_ids and period_ids[0] or False,
            'journal_id': new_asset.category_id.asset_journal_id.id,
            'partner_id': new_asset.supplier_id.id,
            'company_id': new_asset.company_id.id,
        }
        default = vals.copy()
        default['currency_id'] = new_asset.currency_id.id
        asset_obj = self.pool.get('account.asset.asset')
        kwargs = asset_obj._get_move_line_kwargs(cr, uid, new_asset, 'purchase', context)
        line_vals = []
        for line in asset_obj._get_move_lines(cr, uid, default=default, context=context_copy, **kwargs):
            if line.get('asset_id'):
                line_vals.append(line)
                reversal_line = line.copy()
                reversal_line['debit'], reversal_line['credit'] = reversal_line['credit'], reversal_line['debit']
                reversal_line['asset_id'] = old_asset.id
                line_vals.append(reversal_line)
        vals['line_id'] = [(0, 0, x) for x in line_vals]
        move_ids = []
        move_obj = self.pool.get('account.move')
        move_ids.append(move_obj.create(cr, uid, vals, context))
        del vals['line_id']
        vals['journal_id'] = new_asset.category_id.amortization_journal_id and new_asset.category_id.amortization_journal_id.id \
            or new_asset.category_id.asset_journal_id.id
        line_vals = []
        depreciation_line_obj = self.pool.get('account.asset.depreciation.line')
        for line in new_asset.accounting_depreciation_line_ids + new_asset.fiscal_depreciation_line_ids:
            if line.move_id:
                for mline in depreciation_line_obj._get_move_lines(cr, uid, line, default=vals.copy(), context=context_copy):
                    if mline.get('asset_id'):
                        line_vals.append(mline)
                        reversal_line = mline.copy()
                        reversal_line['debit'], reversal_line['credit'] = reversal_line['credit'], reversal_line['debit']
                        reversal_line['asset_id'] = old_asset.id
                        line_vals.append(reversal_line)
        if line_vals:
            vals['line_id'] = [(0, 0, x) for x in line_vals]
            move_ids.append(move_obj.create(cr, uid, vals, context))
        return move_obj.post(cr, uid, move_ids, context)

    def button_validate(self, cr, uid, ids, context=None):
        context = context or {}
        context['do_not_create_account_move_at_validation'] = True
        asset_obj = self.pool.get('account.asset.asset')
        if isinstance(ids, (int, long)):
            ids = [ids]
        for wizard in self.browse(cr, uid, ids, context):
            default = {'parent_id': wizard.asset_id.id, 'purchase_value': wizard.purchase_value,
                       'salvage_value': wizard.salvage_value}
            vals = {'purchase_value': wizard.asset_id.purchase_value - wizard.purchase_value,
                    'salvage_value': wizard.asset_id.salvage_value - wizard.salvage_value}
            if wizard.quantity != wizard.asset_id.quantity:
                default['quantity'] = wizard.quantity
                vals['quantity'] = wizard.asset_id.quantity - wizard.quantity
            new_asset_id = asset_obj.copy(cr, uid, wizard.asset_id.id, default, context)
            wizard.asset_id.write(vals)
            new_asset = asset_obj.browse(cr, uid, new_asset_id, context)
            self._compute_depreciation_board(cr, uid, wizard.asset_id, new_asset, context)
            self._regularize_account_moves(cr, uid, wizard.asset_id, new_asset, context)
        return {'type': 'ir.actions.act_window_close'}
