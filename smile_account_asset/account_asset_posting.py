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

ACCOUNT_GROUPS = {
    'asset_account_id': 'purchase',
    'asset_analytic_account_id': 'purchase',

    'accounting_depreciation_account_id': 'accounting_depreciation',
    'accounting_depreciation_expense_account_id': 'accounting_depreciation',
    'accounting_depreciation_income_account_id': 'accounting_depreciation',

    'fiscal_depreciation_account_id': 'fiscal_depreciation',
    'fiscal_depreciation_expense_account_id': 'fiscal_depreciation',
    'fiscal_depreciation_income_account_id': 'fiscal_depreciation',

    'exceptional_depreciation_account_id': 'exceptional_depreciation',
    'exceptional_depreciation_expense_account_id': 'exceptional_depreciation',
    'exceptional_depreciation_income_account_id': 'exceptional_depreciation',

    'exceptional_amortization_expense_account_id': 'exceptional_amortization',
    'exceptional_amortization_income_account_id': 'exceptional_amortization',
}


class AccountAssetAsset(orm.Model):
    _inherit = 'account.asset.asset'

    def _get_move_line_vals(self, cr, uid, asset, journal_type, amount_excl_tax, tax_amount, tax_ids, accounts=None, default=None, context=None):
        lines = []
        accounts = accounts or {}

        debit, credit = abs(amount_excl_tax), 0.0
        if (amount_excl_tax < 0.0) ^ (journal_type in ('sale', 'purchase_refund')):
            debit, credit = abs(credit), abs(debit)
        asset_line_vals = (default or {}).copy()
        asset_line_vals.update({
            'account_id': accounts['asset_account_id'],
            'debit': debit,
            'credit': credit,
            'asset_id': asset.id,
            'analytic_account_id': accounts['analytic_account_id'],
        })
        lines.append(asset_line_vals)

        if journal_type.startswith('purchase') and asset.invoice_line_ids \
                and asset.invoice_line_ids[0].account_id != asset.category_id.asset_account_id:
            invoice_move_ids = [line.invoice_id.move_id.id for line in asset.invoice_line_ids]
            move_line_obj = self.pool.get('account.move.line')
            for move_line in asset.account_move_line_ids:
                if move_line.move_id.id in invoice_move_ids:
                    reversal_line_vals = move_line_obj.read(cr, uid, move_line.id, context=context, load='_classic_write')
                    reversal_line_vals.update({'debit': move_line.credit, 'credit': move_line.debit})
                    lines.append(reversal_line_vals)
        else:
            if tax_amount:
                tax_line_vals = self.pool.get('account.tax')._get_move_line_vals(cr, uid, tax_ids, amount_excl_tax, journal_type, default, context)
                lines.extend(tax_line_vals)
            debit, credit = 0.0, abs(amount_excl_tax + tax_amount)
            if (amount_excl_tax + tax_amount < 0.0) ^ (journal_type in ('sale', 'purchase_refund')):
                debit, credit = abs(credit), abs(debit)
            partner_line_vals = (default or {}).copy()
            partner_line_vals.update({
                'account_id': accounts['partner_account_id'],
                'debit': debit,
                'credit': credit,
            })
            lines.append(partner_line_vals)
        return lines

    def _get_move_line_kwargs(self, cr, uid, asset, move_type, context=None, reversal=False):
        sign = reversal and -1 or 1
        if move_type == 'purchase':
            if not asset.supplier_id.property_account_payable:
                raise orm.except_orm(_('Error'), _('Please indicate a payable account for the supplier %s') % asset.supplier_id.name)
            return {
                'asset': asset,
                'journal_type': asset.asset_type,
                'amount_excl_tax': asset.purchase_value * sign,
                'tax_amount': asset.purchase_tax_amount * sign,
                'tax_ids': asset.purchase_tax_ids,
                'accounts': {
                    'asset_account_id': asset.category_id.asset_account_id.id,
                    'partner_account_id': asset.supplier_id.property_account_payable.id,
                    'analytic_account_id': asset.category_id.asset_analytic_account_id.id,
                },
            }
        else:
            return {
                'asset': asset,
                'journal_type': asset.asset_type == 'purchase' and 'sale' or 'sale_refund',
                'amount_excl_tax': asset.sale_value * sign,
                'tax_amount': asset.sale_tax_amount * sign,
                'tax_ids': asset.sale_tax_ids,
                'accounts': {
                    'asset_account_id': asset.category_id.sale_income_account_id.id,
                    'partner_account_id': asset.category_id.sale_receivable_account_id.id,
                    'analytic_account_id': asset.category_id.sale_analytic_account_id.id,
                },
            }

    def _get_move_vals(self, cr, uid, asset, move_type, context=None, reversal=False):
        context_copy = context and context.copy() or {}
        context_copy['company_id'] = asset.company_id.id
        today = time.strftime('%Y-%m-%d')
        move_date = asset.purchase_account_date or today
        partner_id = asset.supplier_id.id
        if move_type == 'sale':
            move_date = asset.sale_account_date or today
            partner_id = asset.customer_id.id
        if reversal:
            move_date = today
        msg = move_type == 'purchase' and _('Asset Purchase: %s') or _('Asset Sale: %s')
        journal = move_type == 'sale' and asset.category_id.sale_journal_id or asset.category_id.asset_journal_id
        period_ids = self.pool.get('account.period').find(cr, uid, move_date, context_copy)
        vals = {
            'name': self.pool.get('ir.sequence').next_by_id(cr, uid, journal.sequence_id.id, context),
            'narration': msg % asset.name,
            'ref': asset.code,
            'date': move_date,
            'period_id': period_ids and period_ids[0] or False,
            'journal_id': journal.id,
            'partner_id': partner_id,
            'company_id': asset.company_id.id,
        }
        default = vals.copy()
        default['currency_id'] = asset.currency_id.id
        kwargs = self._get_move_line_kwargs(cr, uid, asset, move_type, context, reversal)
        vals['line_id'] = [(0, 0, x) for x in self._get_move_line_vals(cr, uid, default=default, context=context_copy, **kwargs)]
        return vals

    def create_move(self, cr, uid, ids, move_type, context=None, reversal=False):
        if not ids:
            return True
        assert move_type in ('purchase', 'sale'), "move_type must be equal to 'purchase' or 'sale'"
        move_ids = []
        move_obj = self.pool.get('account.move')
        if isinstance(ids, (int, long)):
            ids = [ids]
        for asset in self.browse(cr, uid, ids, context):
            vals = self._get_move_vals(cr, uid, asset, move_type, context, reversal)
            move_id = move_obj.create(cr, uid, vals, context)
            asset.write({'%s%s_move_id' % (move_type, reversal and '_cancel' or ''): move_id})
            move_ids.append(move_id)
        if move_ids:
            move_obj.post(cr, uid, move_ids, context)
        return True

    def confirm_asset_purchase(self, cr, uid, ids, context=None):
        res = super(AccountAssetAsset, self).confirm_asset_purchase(cr, uid, ids, context)
        context = context or {}
        if not context.get('asset_split'):
            if isinstance(ids, (int, long)):
                ids = [ids]
            for asset in self.browse(cr, uid, ids, context):
                if not asset.invoice_line_ids and (not asset.origin_id or not asset.origin_id.invoice_line_ids):
                    self.create_move(cr, uid, asset.id, 'purchase', context)
        return res

    def cancel_asset_purchase(self, cr, uid, ids, context=None):
        # INFO: Reverse account moves not linked to invoices because these last ones are not canceled
        res = super(AccountAssetAsset, self).cancel_asset_purchase(cr, uid, ids, context)
        depreciation_line_obj = self.pool.get('account.asset.depreciation.line')
        context_copy = context and context.copy() or {}
        context_copy['force_account_move_date'] = time.strftime('%Y-%m-%d')
        if isinstance(ids, (int, long)):
            ids = [ids]
        for asset in self.browse(cr, uid, ids, context=None):
            if 'force_account_move_amount' in context:
                del context['force_account_move_amount']
            if not asset.invoice_line_ids:
                self.create_move(cr, uid, asset.id, 'purchase', context, reversal=True)
            for depreciation_type_field in ('accounting_depreciation_line_ids', 'fiscal_depreciation_line_ids', 'exceptional_depreciation_line_ids'):
                context['force_account_move_amount'] = 0.0
                last_line_id = False
                for line in getattr(asset, depreciation_type_field):  # Because sort by depreciation_date
                    if line.is_posted:
                        context['force_account_move_amount'] += line.depreciation_value
                        last_line_id = line.id
                if last_line_id:
                    depreciation_line_obj.post_depreciation_line(cr, uid, last_line_id, context_copy, reversal=True)
        return res

    def confirm_asset_sale(self, cr, uid, ids, context=None):
        res = super(AccountAssetAsset, self).confirm_asset_sale(cr, uid, ids, context)
        self.create_move(cr, uid, ids, 'sale', context)
        return res

    def cancel_asset_sale(self, cr, uid, ids, context=None):
        # TODO: test me
        # TODO: add a unit test
        if isinstance(ids, (int, long)):
            ids = [ids]
        out_asset_ids = [asset.id for asset in self.browse(cr, uid, ids, context) if asset.is_out]
        self.create_output_moves(cr, uid, out_asset_ids, context, reversal=True)
        self.create_move(cr, uid, ids, 'sale', context, reversal=True)
        return super(AccountAssetAsset, self).cancel_asset_sale(cr, uid, ids, context)

    def _get_inventory_move_tax_lines(self, cr, uid, asset, context=None):
        # TODO: replace the following lines by a unit test
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
            'analytic_account_id': asset.category_id.asset_analytic_account_id.id,
        } for tax_account_id, tax_amount in tax_amounts.items()]

    def _get_inventory_move_lines(self, cr, uid, asset, default=None, context=None, reversal=False):
        accounting_value = exceptional_amortization_value = 0.0
        for line in asset.accounting_depreciation_line_ids:
            if line.is_posted:
                accounting_value += line.depreciation_value
                exceptional_amortization_value += line.book_value_wo_exceptional - line.book_value
        move_lines = [{
            'account_id': asset.category_id.sale_expense_account_id.id,
            'debit': asset.purchase_value - accounting_value - exceptional_amortization_value + asset.regularization_tax_amount,
            'credit': 0.0,
            'asset_id': asset.id,
            'analytic_account_id': asset.category_id.sale_analytic_account_id.id,
        }, {
            'account_id': asset.category_id.accounting_depreciation_account_id.id,
            'debit': accounting_value + exceptional_amortization_value,
            'credit': 0.0,
            'asset_id': asset.id,
            'analytic_account_id': asset.category_id.asset_analytic_account_id.id,
        }, {
            'account_id': asset.category_id.asset_account_id.id,
            'debit': 0.0,
            'credit':  asset.purchase_value,
            'asset_id': asset.id,
            'analytic_account_id': asset.category_id.asset_analytic_account_id.id,
        }]
        if asset.regularization_tax_amount:
            move_lines.extend(self._get_inventory_move_tax_lines(cr, uid, asset, context))
        default = default or {}
        for line in move_lines:
            line.update(default or {})
            if (line['debit'] < 0.0 or line['credit'] < 0.0) ^ reversal:  # ^ means xor
                line['debit'], line['credit'] = abs(line['credit']), abs(line['debit'])
        return move_lines

    def create_inventory_move(self, cr, uid, ids, context=None, reversal=False):
        move_ids = []
        move_obj = self.pool.get('account.move')
        if isinstance(ids, (int, long)):
            ids = [ids]
        context_copy = context and context.copy() or {}
        today = time.strftime('%Y-%m-%d')
        for asset in self.browse(cr, uid, ids, context):
            context_copy['company_id'] = asset.company_id.id
            period_ids = self.pool.get('account.period').find(cr, uid, today, context_copy)
            journal = asset.category_id.asset_journal_id
            vals = {
                'name': self.pool.get('ir.sequence').next_by_id(cr, uid, journal.sequence_id.id, context),
                'narration': _('Asset Output%s: %s') % (reversal and _(' Cancellation') or '', asset.name),
                'ref': asset.code,
                'date': today,
                'period_id': period_ids and period_ids[0] or False,
                'journal_id': journal.id,
                'company_id': asset.company_id.id,
            }
            default = vals.copy()
            default['currency_id'] = asset.currency_id.id
            vals['line_id'] = [(0, 0, x) for x in self._get_inventory_move_lines(cr, uid, asset, default, context)]
            move_ids.append(move_obj.create(cr, uid, vals, context))
        return move_obj.post(cr, uid, move_ids, context)

    def create_output_moves(self, cr, uid, ids, context=None, reversal=False):
        if isinstance(ids, (int, long)):
            ids = [ids]
        # Constater les amortissements/dérogations non encore comptabilisés
        for asset in self.browse(cr, uid, ids, context):
            for line in asset.depreciation_line_ids:
                if not line.is_posted and (line.depreciation_type != 'fiscal' or asset.benefit_accelerated_depreciation):
                    line.post_depreciation_line()
        context = context or {}
        today = time.strftime('%Y-%m-%d')
        depreciation_line_obj = self.pool.get('account.asset.depreciation.line')
        for asset in self.browse(cr, uid, ids, context):
            context['asset_output'] = False
            context['force_account_move_date'] = max(asset.sale_date, today)
            context['asset_output_msg'] = _('Asset Output%s, ') % (reversal and _(' Cancellation') or '')
            # Si mise au rebut, annuler la VNC en tant que dépréciation exceptionnelle
            last_exceptional_value = 0.0
            depreciation_line_id = None
            if asset.sale_type == 'scrapping':
                last_exceptional_value += asset.book_value
                depreciation_line_id = depreciation_line_obj.create(cr, uid, {
                    'asset_id': asset.id,
                    'depreciation_type': 'exceptional',
                    'depreciation_date': context['force_account_move_date'],
                    'depreciation_value': last_exceptional_value,
                }, context)
                depreciation_line_obj.post_depreciation_line(cr, uid, depreciation_line_id, context)
                self._store_set_values(cr, uid, [asset.id], ['book_value'], context)
            # Annuler les dépréciations (exceptional_value)
            context['asset_output'] = True
            exceptional_value = sum([line.depreciation_value for line in asset.exceptional_depreciation_line_ids if line.is_posted])
            if exceptional_value:
                context['force_account_move_amount'] = exceptional_value * -1
                asset.exceptional_depreciation_line_ids[-1].post_depreciation_line()
            # Annuler les amortissements dérogatoires (accelerated_value)
            accelerated_value = sum([line.accelerated_value for line in asset.fiscal_depreciation_line_ids if line.is_posted])
            if accelerated_value:
                context['force_account_move_amount'] = accelerated_value * -1
                asset.fiscal_depreciation_line_ids[-1].post_depreciation_line()
            # Annuler l'immobilisation et les amortissements comptables (accounting_value), et constater la TVA à reverser
            asset.create_inventory_move()

    def output(self, cr, uid, ids, context=None, reversal=False):
        res = super(AccountAssetAsset, self).output(cr, uid, ids, context)
        self.create_output_moves(cr, uid, ids, context)
        return res

    def _get_changed_accounts(self, cr, uid, old_values, new_values, context=None):
        assert sorted(old_values.keys()) == sorted(new_values.keys()), "old_values and new_values must have the same keys!"
        accounts_by_group = {}
        for account in new_values:
            if account in ACCOUNT_GROUPS and old_values[account] and old_values[account] != new_values[account]:
                group = ACCOUNT_GROUPS[account]
                accounts_by_group.setdefault(group, {})
                accounts_by_group[group][account] = new_values[account]
        return accounts_by_group

    def _get_group_accounts(self, cr, uid, group, old_values, new_values, context):
        old_accounts, new_accounts = {}, {}
        for account in ACCOUNT_GROUPS:
            if ACCOUNT_GROUPS[account] == group and account in old_values:
                # old_values[account] != new_values[account] is implicit, see _get_changed_accounts
                old_accounts[account] = old_values[account]
                new_accounts[account] = new_values[account]
        return old_accounts, new_accounts

    def change_accounts(self, cr, uid, relation, old_values, new_values, context=None):
        # TODO: manage exceptional amortization accounts change
        accounts_by_group = self._get_changed_accounts(cr, uid, old_values, new_values, context)
        relation_model, relation_id = relation.split(',')
        relation_id = int(relation_id)
        if relation_model == 'res.company':
            relation_field = 'company_id'
        elif relation_model == 'account.asset.category':
            relation_field = 'category_id'
        else:
            relation_field = 'id'
        depreciation_line_obj = self.pool.get('account.asset.depreciation.line')
        for group in accounts_by_group:
            old_accounts, new_accounts = self._get_group_accounts(cr, uid, group, old_values, new_values, context)
            if group == 'purchase':
                asset_ids = self.search(cr, uid, [
                    (relation_field, '=', relation_id),
                    ('state', 'in', ['confirm', 'open']),
                ], context=context)
                self._transfer_from_accounts_to_others(cr, uid, asset_ids, group, old_accounts, new_accounts, context)
            else:
                depreciation_type = group.replace('_depreciation', '')
                if group == "exceptional_amortization":
                    depreciation_type = 'accounting'
                if relation_field == 'id':
                    relation_field = 'asset_id'
                domain = [
                    (relation_field, '=', relation_id),
                    ('depreciation_type', '=', depreciation_type),
                    ('is_posted', '=', True),
                ]
                if depreciation_type == 'fiscal':
                    domain.append(('benefit_accelerated_depreciation', '=', True))
                depreciation_line_ids = depreciation_line_obj.search(cr, uid, domain, context=context)
                depreciation_line_obj._transfer_from_accounts_to_others(cr, uid, depreciation_line_ids, group, old_accounts, new_accounts, context)
        return True

    def _transfer_from_accounts_to_others(self, cr, uid, ids, accounts_group, old_accounts, new_accounts, context=None):
        move_ids = []
        move_obj = self.pool.get('account.move')
        analytic_field = 'asset_analytic_account_id' if accounts_group == 'purchase' else 'sale_analytic_account_id'
        context_copy = context and context.copy() or {}
        context_copy['force_account_move_date'] = time.strftime('%Y-%m-%d')
        for asset in self.browse(cr, uid, ids, context):
            vals = self._get_move_vals(cr, uid, asset, accounts_group, context_copy)
            new_line_vals = []
            for i, j, line_vals in vals['line_id']:
                for account, group in ACCOUNT_GROUPS.iteritems():
                    if group != accounts_group or account not in old_accounts or 'analytic' in account:
                        continue
                    if line_vals['account_id'] == old_accounts[account] or (analytic_field in old_accounts and analytic_field in line_vals):
                        transfer_vals = line_vals.copy()
                        if account in new_accounts:
                            transfer_vals['account_id'] = new_accounts[account]
                        if analytic_field in new_accounts:
                            transfer_vals['analytic_account_id'] = new_accounts[analytic_field]
                        line_vals['debit'], line_vals['credit'] = line_vals['credit'], line_vals['debit']
                        new_line_vals.extend([(0, 0, transfer_vals), (0, 0, line_vals)])
                        break
            vals['line_id'] = new_line_vals
            move_ids.append(move_obj.create(cr, uid, vals, context))
        if move_ids:
            return move_obj.post(cr, uid, move_ids, context)
        return True

    def _compute_depreciation_lines(self, cr, uid, asset_id, depreciation_type='accounting', context=None):
        sale_date = self.read(cr, uid, asset_id, ['sale_date'], context)['sale_date']
        if sale_date:
            depreciation_line_obj = self.pool.get('account.asset.depreciation.line')
            line_ids_to_reversal_and_delete = depreciation_line_obj.search(cr, uid, [('asset_id', '=', asset_id),
                                                                                     ('depreciation_date', '>', sale_date),
                                                                                     ('depreciation_type', '=', depreciation_type),
                                                                                     ('is_posted', '=', True)], context=context)
            depreciation_line_obj.post_depreciation_line(cr, uid, line_ids_to_reversal_and_delete, context, reversal=True)
            depreciation_line_obj.unlink(cr, uid, line_ids_to_reversal_and_delete, context)
        return super(AccountAssetAsset, self)._compute_depreciation_lines(cr, uid, asset_id, depreciation_type, context)


class AccountAssetDepreciationLine(orm.Model):
    _inherit = 'account.asset.depreciation.line'

    def _get_move_line_vals(self, cr, uid, line, default=None, context=None, reversal=False, transfer=None):
        context = context or {}
        asset = line.asset_id
        amount = line.depreciation_value
        second_related_object = None
        if line.depreciation_type == 'accounting' and not transfer:
            main_related_object = asset.category_id
            account_field = 'accounting_depreciation_account_id'
            expense_account_field = 'accounting_depreciation_expense_account_id'
            income_account_field = 'accounting_depreciation_income_account_id'
        elif line.depreciation_type == 'fiscal':
            if not asset.company_id.fiscal_depreciation_expense_account_id or \
                    not asset.company_id.fiscal_depreciation_income_account_id or \
                    not asset.company_id.fiscal_depreciation_account_id:
                raise orm.except_orm(_('Error'), _('Please indicate fiscal amortization accounts in company form!'))
            main_related_object = asset.company_id
            amount = line.accelerated_value
            account_field = 'fiscal_depreciation_account_id'
            expense_account_field = 'fiscal_depreciation_expense_account_id'
            income_account_field = 'fiscal_depreciation_income_account_id'
        else:  # elif line.depreciation_type == 'exceptional':
            main_related_object = asset.category_id
            account_field = 'exceptional_depreciation_account_id'
            expense_account_field = 'exceptional_depreciation_expense_account_id'
            income_account_field = 'exceptional_depreciation_income_account_id'
        if transfer:
            if not asset.company_id.exceptional_amortization_expense_account_id or \
                    not asset.company_id.exceptional_amortization_income_account_id:
                raise orm.except_orm(_('Error'), _('Please indicate exceptional amortization accounts in company form!'))
            amount = line.book_value_wo_exceptional - line.book_value  # INFO: always >= 0.0 by defintion, see French law
            if transfer == 'from_depreciation':
                main_related_object = asset.category_id
                second_related_object = asset.company_id
                account_field = 'exceptional_depreciation_account_id'
                expense_account_field = 'exceptional_amortization_expense_account_id'
            else:  # elif transfer == 'to_exceptional_amortization':
                amount *= -1.0
                main_related_object = asset.category_id
                second_related_object = asset.company_id
                account_field = 'accounting_depreciation_account_id'
                income_account_field = 'exceptional_amortization_income_account_id'
        if context.get('force_account_move_amount'):
            amount = context['force_account_move_amount']
        debit, credit = 0.0, abs(amount)
        if line.asset_type == 'purchase_refund':
            debit, credit = credit, debit
        if (amount < 0.0) ^ reversal:  # ^ means xor
            debit, credit = abs(credit), abs(debit)
        default = default or {}
        default.update({
            'partner_id': asset.supplier_id.id,
            'currency_id': asset.currency_id.id,
        })
        depreciation_line_vals = default.copy()
        depreciation_line_vals.update({
            'debit': debit,
            'credit': credit,
            'account_id': getattr(main_related_object, account_field).id,
            'analytic_account_id': asset.category_id.asset_analytic_account_id.id,
            'asset_id': asset.id,
        })
        expense_or_income_line_vals = default.copy()
        expense_or_income_line_vals.update({
            'debit': credit,
            'credit': debit,
            'account_id': getattr(second_related_object or main_related_object, amount > 0 and expense_account_field or income_account_field).id,
        })
        return [depreciation_line_vals, expense_or_income_line_vals]

    def _get_move_vals(self, cr, uid, line, context=None, reversal=False, transfer=None):
        asset = line.asset_id
        category = asset.category_id
        context_copy = context and context.copy() or {}
        context_copy['company_id'] = line.asset_id.company_id.id
        move_date = context.get('force_account_move_date') or line.depreciation_date
        period_ids = self.pool.get('account.period').find(cr, uid, move_date, context_copy)
        msg = ''
        if line.depreciation_type == 'accounting' and not transfer:
            msg = _('Accounting Amortization')
        elif line.depreciation_type == 'fiscal':
            msg = _('Fiscal Amortization')
        elif line.depreciation_type == 'exceptional':
            msg = _('Exceptional Depreciation')
        elif transfer:
            msg = _('Exceptional Amortization')
        prefix = context.get('asset_output_msg', '')
        journal = category.depreciation_journal_id or category.asset_journal_id
        vals = {
            'name': self.pool.get('ir.sequence').next_by_id(cr, uid, journal.sequence_id.id, context),
            'narration': '%s%s: %s' % (prefix, msg, asset.name),
            'ref': asset.code,
            'date': move_date,
            'period_id': period_ids and period_ids[0] or False,
            'journal_id': journal.id,
            'company_id': asset.company_id.id,
        }
        vals['line_id'] = [(0, 0, x) for x in self._get_move_line_vals(cr, uid, line, default=vals.copy(), context=context,
                                                                       reversal=reversal, transfer=transfer)]
        return vals

    def post_depreciation_line(self, cr, uid, ids, context=None, reversal=False):
        if not ids:
            return True
        move_ids = []
        move_obj = self.pool.get('account.move')
        if isinstance(ids, (int, long)):
            ids = [ids]
        context = context or {}
        for line in self.browse(cr, uid, ids, context):
            if (line.move_id or line.is_posted) and not (context.get('asset_output') or reversal):
                continue
            if line.depreciation_type == 'fiscal' and not line.asset_id.benefit_accelerated_depreciation:
                continue
            vals = self._get_move_vals(cr, uid, line, context, reversal)
            move_id = move_obj.create(cr, uid, vals, context)
            move_ids.append(move_id)
            if not context.get('asset_output'):
                line.write({'move_id': move_id})
                if not reversal and line.depreciation_type == 'accounting' and line.book_value != line.book_value_wo_exceptional:
                    vals = self._get_move_vals(cr, uid, line, context, reversal, transfer='from_depreciation')
                    move_obj.create(cr, uid, vals, context)
                    vals = self._get_move_vals(cr, uid, line, context, reversal, transfer='to_exceptional_amortization')
                    move_obj.create(cr, uid, vals, context)
        if move_ids:
            move_obj.post(cr, uid, move_ids, context)
        return True

    def validate_exceptional_depreciation(self, cr, uid, ids, context=None):
        super(AccountAssetDepreciationLine, self).validate_exceptional_depreciation(cr, uid, ids, context)
        return self.post_depreciation_line(cr, uid, ids, context)

    def _transfer_from_accounts_to_others(self, cr, uid, ids, accounts_group, old_accounts, new_accounts, context=None):
        move_ids = []
        move_obj = self.pool.get('account.move')
        today = time.strftime('%Y-%m-%d')
        last_depreciation_line_by_asset = {}
        for depreciation_line in self.browse(cr, uid, ids, context):
            amount_field = 'depreciation_value' if depreciation_line.depreciation_type != 'fiscal' else 'accelerated_value'
            last_depreciation_line_by_asset.setdefault(depreciation_line.asset_id.id, [depreciation_line, 0.0])
            last_depreciation_line_by_asset[depreciation_line.asset_id.id][0] = depreciation_line
            last_depreciation_line_by_asset[depreciation_line.asset_id.id][1] += getattr(depreciation_line, amount_field)
        context_copy = context and context.copy() or {}
        for depreciation_line, amount in last_depreciation_line_by_asset.itervalues():
            context_copy['force_account_move_amount'] = amount
            context_copy['force_account_move_date'] = today
            transfer_groups = ['']
            if accounts_group == 'exceptional_amortization':
                transfer_groups = ['from_depreciation', 'to_exceptional_amortization']
            for transfer in transfer_groups:
                vals = self._get_move_vals(cr, uid, depreciation_line, context_copy, transfer=transfer)
                new_line_vals = []
                for i, j, line_vals in vals['line_id']:
                    for account, group in ACCOUNT_GROUPS.iteritems():
                        if group == accounts_group and account in old_accounts and line_vals['account_id'] == old_accounts[account]:
                            transfer_vals = line_vals.copy()
                            transfer_vals['account_id'] = new_accounts[account]
                            line_vals['debit'], line_vals['credit'] = line_vals['credit'], line_vals['debit']
                            new_line_vals.extend([(0, 0, transfer_vals), (0, 0, line_vals)])
                            break
                vals['line_id'] = new_line_vals
                move_ids.append(move_obj.create(cr, uid, vals, context))
        if move_ids:
            return move_obj.post(cr, uid, move_ids, context)
        return True


class AccountAssetHistory(orm.Model):
    _inherit = 'account.asset.history'

    def _get_values(self, cr, uid, vals, context=None):
        old_vals, new_vals = super(AccountAssetHistory, self)._get_values(cr, uid, vals, context)
        if old_vals['category_id'] != new_vals['category_id']:
            asset_obj = self.pool.get('account.asset.asset')
            category_obj = self.pool.get('account.asset.category')
            old_values = category_obj.read(cr, uid, old_vals['category_id'], [], context, '_classic_write')
            new_values = category_obj.read(cr, uid, new_vals['category_id'], [], context, '_classic_write')
            asset_obj.change_accounts(cr, uid, '%s,%s' % (asset_obj._name, vals['asset_id']), old_values, new_values, context)
        return old_vals, new_vals
