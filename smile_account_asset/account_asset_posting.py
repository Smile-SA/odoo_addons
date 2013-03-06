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

from osv import orm
from tools.translate import _


class AccountAssetAsset(orm.Model):
    _inherit = 'account.asset.asset'

    def _get_move_lines(self, cr, uid, asset, journal_type, amount_excl_tax, tax_amount, tax_ids, accounts=None, default=None, context=None):
        lines = []
        accounts = accounts or {}

        debit, credit = amount_excl_tax, 0.0
        if journal_type in ('sale', 'purchase_refund'):
            debit, credit = credit, debit
        asset_line_vals = (default or {}).copy()
        asset_line_vals.update({
            'account_id': accounts['product_account_id'],
            'debit': debit,
            'credit': credit,
            'asset_id': asset.id,
            'analytic_account_id': accounts['analytic_account_id'],
        })
        lines.append(asset_line_vals)

        if journal_type.startswith('purchase') and asset.invoice_line_ids and asset.invoice_line_ids[0].account_id != asset.asset_account_id:
            invoice_move_ids = [line.invoice_id.move_id.id for line in asset.invoice_line_ids]
            move_line_obj = self.pool.get('account.move.line')
            for move_line in asset.account_move_line_ids:
                if move_line.move_id.id in invoice_move_ids:
                    reversal_line_vals = move_line_obj.read(cr, uid, move_line.id, context=context, load='_classic_write')
                    reversal_line_vals.update({'debit': move_line.credit, 'credit': move_line.debit})
                    lines.append(reversal_line_vals)
        else:
            if tax_amount:
                lines.extend(self.pool.get('account.tax')._get_move_lines(cr, uid, tax_ids, amount_excl_tax, journal_type, default, context))
            debit, credit = 0.0, amount_excl_tax + tax_amount
            if journal_type in ('sale', 'purchase_refund'):
                debit, credit = credit, debit
            partner_line_vals = (default or {}).copy()
            partner_line_vals.update({
                'account_id': accounts['partner_account_id'],
                'debit': debit,
                'credit': credit,
            })
            lines.append(partner_line_vals)
        return lines

    def _get_move_line_kwargs(self, cr, uid, asset, move_type, context=None):
        if move_type == 'purchase':
            return {
                'asset': asset,
                'journal_type': asset.asset_type,
                'amount_excl_tax': asset.purchase_value,
                'tax_amount': asset.purchase_tax_amount,
                'tax_ids': asset.purchase_tax_ids,
                'accounts': {
                    'product_account_id': asset.category_id.asset_account_id.id,
                    'partner_account_id': asset.supplier_id.property_account_payable.id,
                    'analytic_account_id': asset.category_id.analytic_account_id and
                    asset.category_id.analytic_account_id.id or False,
                },
            }
        else:
            return {
                'asset': asset,
                'journal_type': asset.asset_type == 'purchase' and 'sale' or 'sale_refund',
                'amount_excl_tax': asset.sale_value,
                'tax_amount': asset.sale_tax_amount,
                'tax_ids': asset.sale_tax_ids,
                'accounts': {
                    'product_account_id': asset.category_id.disposal_income_account_id.id,
                    'partner_account_id': asset.category_id.disposal_receivable_account_id.id,
                    'analytic_account_id': asset.category_id.disposal_analytic_account_id and
                    asset.category_id.disposal_analytic_account_id.id or False,
                },
            }

    def create_move(self, cr, uid, ids, move_type, context=None):
        assert move_type in ('purchase', 'sale'), "move_type must be equal to 'purchase' or 'sale'"
        msg = move_type == 'purchase' and _('Asset Purchase: %s') or _('Asset Sale: %s')
        move_ids = []
        move_obj = self.pool.get('account.move')
        context_copy = (context or {}).copy()
        if isinstance(ids, (int, long)):
            ids = [ids]
        for asset in self.browse(cr, uid, ids, context):
            context_copy['company_id'] = asset.company_id.id
            period_ids = self.pool.get('account.period').find(cr, uid, asset.depreciation_date_start, context_copy)
            date = asset.validation_date
            partner_id = asset.supplier_id.id
            if move_type == 'sale':
                date = asset.sale_date
                partner_id = asset.customer_id.id
            vals = {
                'name': msg % asset.name,
                'ref': asset.code,
                'date': date or time.strftime('%Y-%m-%d'),
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': asset.category_id.asset_journal_id.id,
                'partner_id': partner_id,
                'company_id': asset.company_id.id,
            }
            default = vals.copy()
            default['currency_id'] = asset.currency_id.id
            kwargs = self._get_move_line_kwargs(cr, uid, asset, move_type, context)
            vals['line_id'] = [(0, 0, x) for x in self._get_move_lines(cr, uid, default=default, context=context_copy, **kwargs)]
            move_ids.append(move_obj.create(cr, uid, vals, context))
        if move_ids:
            return move_obj.post(cr, uid, move_ids, context)
        return True

    def validate(self, cr, uid, ids, context=None):
        super(AccountAssetAsset, self).validate(cr, uid, ids, context)
        context = context or {}
        if context.get('do_not_create_account_move_at_validation'):
            return True
        if isinstance(ids, (int, long)):
            ids = [ids]
        asset_ids = []
        for asset in self.browse(cr, uid, ids, context):
            if not asset.invoice_line_ids or asset.invoice_line_ids[0].account_id != asset.asset_account_id:
                asset_ids.append(asset.id)
        if asset_ids:
            return self.create_move(cr, uid, asset_ids, 'purchase', context)
        return True

    def confirm_asset_sale(self, cr, uid, ids, context=None):
        super(AccountAssetAsset, self).confirm_asset_sale(cr, uid, ids, context)
        return self.create_move(cr, uid, ids, 'sale', context)

    def _get_inventory_move_tax_lines(self, cr, uid, asset, context=None):
        tax_amounts = {}
        taxes = self.pool.get('account.tax').compute_all(cr, uid, asset.purchase_tax_ids, asset.purchase_value, 1.0)['taxes']
        for tax in taxes:
            tax_amounts.setdefault(tax['account_collected_id'], 0.0)
            tax_amounts[tax['account_collected_id']] += tax['amount']
        regularization_coeff = self._get_regularization_tax_coeff(cr, uid, asset, context)
        return [{
            'account_id': tax_account_id,
            'debit': 0.0,
            'credit': tax_amount * regularization_coeff,
            'analytic_account_id': asset.category_id.analytic_account_id and asset.category_id.analytic_account_id.id or False,
        } for tax_account_id, tax_amount in tax_amounts.items()]

    def _get_inventory_move_lines(self, cr, uid, asset, default=None, context=None):
        move_lines = [{
            'account_id': asset.category_id.disposal_expense_account_id.id,
            'debit': asset.book_value + asset.regularization_tax_amount,
            'credit': 0.0,
            'asset_id': asset.id,
            'analytic_account_id': asset.category_id.disposal_analytic_account_id and asset.category_id.disposal_analytic_account_id.id or False,
        }, {
            'account_id': asset.category_id.amortization_account_id.id,
            'debit': asset.accumulated_amortization_value,
            'credit': 0.0,
            'asset_id': asset.id,
            'analytic_account_id': asset.category_id.analytic_account_id and asset.category_id.analytic_account_id.id or False,
        }, {
            'account_id': asset.category_id.asset_account_id.id,
            'debit': 0.0,
            'credit':  asset.purchase_value,
            'asset_id': asset.id,
            'analytic_account_id': asset.category_id.analytic_account_id and asset.category_id.analytic_account_id.id or False,
        }]
        if asset.regularization_tax_amount:
            move_lines.extend(self._get_inventory_move_tax_lines(cr, uid, asset, context))
        default = default or {}
        for line in move_lines:
            line.update(default or {})
            if line['debit'] < 0.0 or line['credit'] < 0.0:
                line['debit'], line['credit'] = abs(line['credit']), abs(line['debit'])
        return move_lines

    def create_inventory_move(self, cr, uid, ids, context=None):
        move_ids = []
        move_obj = self.pool.get('account.move')
        context_copy = (context or {}).copy()
        if isinstance(ids, (int, long)):
            ids = [ids]
        for asset in self.browse(cr, uid, ids, context):
            context_copy['company_id'] = asset.company_id.id
            period_ids = self.pool.get('account.period').find(cr, uid, asset.depreciation_date_start, context_copy)
            vals = {
                'name': _('Asset Output: %s') % asset.name,
                'ref': asset.code,
                'date': time.strftime('%Y-%m-%d'),
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': asset.category_id.asset_journal_id.id,
                'company_id': asset.company_id.id,
            }
            default = vals.copy()
            default['currency_id'] = asset.currency_id.id
            vals['line_id'] = [(0, 0, x) for x in self._get_inventory_move_lines(cr, uid, asset, default, context)]
            move_ids.append(move_obj.create(cr, uid, vals, context))
        return move_obj.post(cr, uid, move_ids, context)

    def output(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for asset in self.browse(cr, uid, ids, context):
            # Constater les amortissements/dérogations non encore comptabilisés
            # WARNING: Les amortissements comptable et dérogatoire complémentaires vont être constatés
            # dès la clôture de la période comptable de la cession. Vérifier que comptablement parlant
            # ce n'est pas un problème
            for line in asset.depreciation_line_ids:
                if not line.move_id and (line.depreciation_type != 'fiscal' or line.depreciation_value):
                    line.post_depreciation_line()
        context = context or {}
        context['asset_output'] = True
        context['force_account_move_date'] = time.strftime('%Y-%m-%d')
        for asset in self.browse(cr, uid, ids, context):
            context['asset_output_msg'] = _('Asset Output: %s') % asset.name
            # Annuler les dépréciations (exceptional_value)
            exceptional_value = [line.depreciation_value for line in asset.exceptional_depreciation_line_ids if not line.move_id]
            if exceptional_value:
                context['force_account_move_amount'] = exceptional_value * -1
                asset.exceptional_depreciation_line_ids[-1].post_depreciation_line()
            # Annuler les amortissements dérogatoires (accelerated_value)
            accelerated_value = [line.accelerated_value for line in asset.fiscal_depreciation_line_ids if not line.move_id]
            if accelerated_value:
                context['force_account_move_amount'] = accelerated_value * -1
                asset.fiscal_depreciation_line_ids[-1].post_depreciation_line()
            # Annuler l'immobilisation et les amortissements comptables (accounting_value), et constater la TVA à reverser
            asset.create_inventory_move()
        return super(AccountAssetAsset, self).output(cr, uid, ids, context)


class AccountAssetDepreciationLine(orm.Model):
    _inherit = 'account.asset.depreciation.line'

    def _get_move_lines(self, cr, uid, depreciation_line, default=None, context=None):
        context = context or {}
        asset = depreciation_line.asset_id
        amount = depreciation_line.depreciation_value
        if depreciation_line.depreciation_type == 'accounting':
            account_field = 'amortization_account_id'
            expense_account_field = 'amortization_expense_account_id'
            income_account_field = 'amortization_income_account_id'
        elif depreciation_line.depreciation_type == 'fiscal':
            amount = depreciation_line.accelerated_value
            account_field = 'fiscal_depreciation_account_id'
            expense_account_field = 'fiscal_depreciation_expense_account_id'
            income_account_field = 'fiscal_depreciation_income_account_id'
        else:  # elif depreciation_line.depreciation_type == 'exceptional':
            account_field = 'depreciation_account_id'
            expense_account_field = 'depreciation_expense_account_id'
            income_account_field = 'depreciation_income_account_id'
        if context.get('force_account_move_amount'):
            amount = context['force_account_move_amount']
        debit, credit = 0.0, amount
        if depreciation_line.asset_type == 'purchase_refund':
            debit, credit = credit, debit
        if amount < 0.0:
            debit, credit = abs(credit), abs(debit)
        default = default or {}
        default.update({
            'partner_id': asset.supplier_id.id,
            'currency_id': asset.currency_id.id,
        })
        depreciation_line_vals = default.copy()
        depreciation_line_vals.update({
            'account_id': getattr(depreciation_line.depreciation_type == 'fiscal' and asset.company_id or asset.category_id, account_field).id,
            'debit': credit,
            'credit': debit,
        })
        expense_or_income_line_vals = default.copy()
        expense_or_income_line_vals.update({
            'account_id': getattr(depreciation_line.depreciation_type == 'fiscal' and asset.company_id or asset.category_id,
                                  amount > 0 and expense_account_field or income_account_field).id,
            'debit': debit,
            'credit': credit,
            'asset_id': asset.id,
            'analytic_account_id': asset.category_id.analytic_account_id and asset.category_id.analytic_account_id.id or False,
        })
        return [depreciation_line_vals, expense_or_income_line_vals]

    def post_depreciation_line(self, cr, uid, ids, context=None):
        context_copy = (context or {}).copy()
        move_ids = []
        move_obj = self.pool.get('account.move')
        if isinstance(ids, (int, long)):
            ids = [ids]
        for depreciation_line in self.browse(cr, uid, ids, context):
            if not context_copy.get('asset_output') and depreciation_line.move_id:
                continue
            asset = depreciation_line.asset_id
            context_copy['company_id'] = depreciation_line.asset_id.company_id.id
            period_ids = self.pool.get('account.period').find(cr, uid, depreciation_line.depreciation_date, context_copy)
            msg = '%s'
            if depreciation_line.depreciation_type == 'accounting':
                msg = _('Accounting Amortization: %s')
            elif depreciation_line.depreciation_type == 'fiscal':
                msg = _('Fiscal Amortization: %s')
            elif depreciation_line.depreciation_type == 'exceptional':
                msg = _('Exceptional Depreciation: %s')
            vals = {
                'name': context_copy.get('asset_output_msg') and '%s, %s' % (context_copy['asset_output_msg'], msg[:-4]) or msg % asset.name,
                'ref': asset.code,
                'date': context_copy.get('force_account_move_date') or depreciation_line.depreciation_date,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': asset.category_id.amortization_journal_id and asset.category_id.amortization_journal_id.id
                or asset.category_id.asset_journal_id.id,
                'company_id': asset.company_id.id,
            }
            vals['line_id'] = [(0, 0, x) for x in self._get_move_lines(cr, uid, depreciation_line, default=vals.copy(), context=context_copy)]
            move_id = move_obj.create(cr, uid, vals, context)
            if not context_copy.get('asset_output'):
                depreciation_line.write({'move_id': move_id})
            move_ids.append(move_id)
        if move_ids:
            move_obj.post(cr, uid, move_ids, context)
        return True

    def validate_exceptional_depreciation(self, cr, uid, ids, context=None):
        super(AccountAssetDepreciationLine, self).validate_exceptional_depreciation(cr, uid, ids, context)
        return self.post_depreciation_line(cr, uid, ids, context)
