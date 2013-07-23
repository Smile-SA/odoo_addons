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

from osv import orm, fields
from tools.translate import _


class AccountMove(orm.Model):
    _inherit = 'account.move'

    _columns = {
        'asset_depreciation_line_ids': fields.one2many('account.asset.depreciation.line', 'move_id', 'Asset Depreciation Lines', readonly=True),
    }

    def copy_data(self, cr, uid, move_id, default=None, context=None):
        default = default or {}
        default['asset_depreciation_line_ids'] = []
        return super(AccountMove, self).copy_data(cr, uid, move_id, default, context=context)


class AccountTax(orm.Model):
    _inherit = 'account.tax'

    def _get_move_line_vals(self, cr, uid, taxes, amount_excl_tax, journal_type, default=None, context=None):
        lines = []
        for tax_info in self.compute_all(cr, uid, taxes, amount_excl_tax, 1.0)['taxes']:
            if tax_info['amount']:
                tax_line_vals = (default or {}).copy()
                tax_line_vals.update({
                    'tax_code_id': tax_info['tax_code_id'],
                    'tax_amount': tax_info['amount'] * tax_info['_refund' in journal_type and 'ref_base_sign' or 'base_sign'],
                })
                debit, credit = 0.0, tax_info['amount']
                if tax_info['amount'] < 0.0:
                    debit, credit = abs(credit), abs(debit)
                if journal_type in ('purchase_refund', 'sale'):
                    if not tax_info['account_collected_id']:
                        raise orm.except_orm(_('Error'), _('Please indicate a collected tax account for %s!') % tax_info['name'])
                    tax_line_vals.update({
                        'account_id': tax_info['account_collected_id'],
                        'debit': debit,
                        'credit': credit,
                    })
                elif journal_type in ('purchase', 'sale_refund'):
                    if not tax_info['account_paid_id']:
                        raise orm.except_orm(_('Error'), _('Please indicate a paid tax account for %s!') % tax_info['name'])
                    tax_line_vals.update({
                        'account_id': tax_info['account_paid_id'],
                        'debit': credit,
                        'credit': debit,
                    })
                lines.append(tax_line_vals)
        return lines


class AccountPeriod(orm.Model):
    _inherit = 'account.period'

    def post_depreciation_line(self, cr, uid, ids, context=None):
        depreciation_line_obj = self.pool.get('account.asset.depreciation.line')
        if isinstance(ids, (int, long)):
            ids = [ids]
        for period in self.browse(cr, uid, ids, context):
            depreciation_line_ids = depreciation_line_obj.search(cr, uid, [
                ('depreciation_date', '>=', period.date_start),
                ('depreciation_date', '<=', period.date_stop),
                ('move_id', '=', False),
            ], context=context)
            depreciation_line_obj.post_depreciation_line(cr, uid, depreciation_line_ids, context)
        return True


class AccountFiscalYear(orm.Model):
    _inherit = 'account.fiscalyear'

    def create_inventory_entry(self, cr, uid, ids, context=None):
        asset_obj = self.pool.get('account.asset.asset')
        if isinstance(ids, (int, long)):
            ids = [ids]
        for fiscalyear in self.browse(cr, uid, ids, context):
            asset_ids = asset_obj.search(cr, uid, [
                ('sale_date', '>=', fiscalyear.date_start),
                ('sale_date', '<=', fiscalyear.date_stop),
                ('state', '=', 'close'),
                ('is_out', '=', False),
            ], context=context)
            asset_obj.output(cr, uid, asset_ids, context)
        return True
