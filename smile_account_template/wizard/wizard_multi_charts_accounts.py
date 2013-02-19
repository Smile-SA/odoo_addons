# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging

from osv import osv
from tools.translate import _


class MultiAccountsChartsWizard(osv.osv_memory):
    _inherit = 'wizard.multi.charts.accounts'

    def __init__(self, pool, cr):
        super(MultiAccountsChartsWizard, self).__init__(pool, cr)
        self._logger = logging.getLogger('MultiAccountsChartsWizard')

    def _create_taxes(self, cr, uid, obj_multi, context=None):
        self._logger.info('loading taxes')
        todo_dict = {}
        obj_acc_tax = self.pool.get('account.tax')
        obj_tax_code = self.pool.get('account.tax.code')
        tax_template_ref = {}
        tax_code_template_ref = {}
        tax_code_root_id = obj_multi.chart_template_id.tax_code_root_id.id
        company_id = obj_multi.company_id.id
        # create all the tax code
        children_tax_code_template = self.pool.get('account.tax.code.template').search(cr, uid, [('parent_id', 'child_of', [tax_code_root_id])],
                                                                                       order='id', context=context)
        children_tax_code_template.sort()
        for tax_code_template in self.pool.get('account.tax.code.template').browse(cr, uid, children_tax_code_template, context):
            vals = {
                'name': (tax_code_root_id == tax_code_template.id) and obj_multi.company_id.name or tax_code_template.name,
                'code': tax_code_template.code,
                'info': tax_code_template.info,
                'parent_id': tax_code_template.parent_id and ((tax_code_template.parent_id.id in tax_code_template_ref)
                                                              and tax_code_template_ref[tax_code_template.parent_id.id]) or False,
                'company_id': company_id,
                'sign': tax_code_template.sign,
            }
            new_tax_code = obj_tax_code.create(cr, uid, vals)
            # recording the new tax code to do the mapping
            tax_code_template_ref[tax_code_template.id] = new_tax_code
        # create all the tax
        tax_template_to_tax = {}
        for tax in obj_multi.chart_template_id.tax_template_ids:
            # create it
            vals_tax = {
                'name': tax.name,
                'sequence': tax.sequence,
                'amount': tax.amount,
                'type': tax.type,
                'applicable_type': tax.applicable_type,
                'domain': tax.domain,
                'parent_id': tax.parent_id and ((tax.parent_id.id in tax_template_ref)
                                                and tax_template_ref[tax.parent_id.id]) or False,
                'child_depend': tax.child_depend,
                'python_compute': tax.python_compute,
                'python_compute_inv': tax.python_compute_inv,
                'python_applicable': tax.python_applicable,
                'base_code_id': tax.base_code_id and ((tax.base_code_id.id in tax_code_template_ref)
                                                      and tax_code_template_ref[tax.base_code_id.id]) or False,
                'tax_code_id': tax.tax_code_id and ((tax.tax_code_id.id in tax_code_template_ref)
                                                    and tax_code_template_ref[tax.tax_code_id.id]) or False,
                'base_sign': tax.base_sign,
                'tax_sign': tax.tax_sign,
                'ref_base_code_id': tax.ref_base_code_id and ((tax.ref_base_code_id.id in tax_code_template_ref)
                                                              and tax_code_template_ref[tax.ref_base_code_id.id]) or False,
                'ref_tax_code_id': tax.ref_tax_code_id and ((tax.ref_tax_code_id.id in tax_code_template_ref)
                                                            and tax_code_template_ref[tax.ref_tax_code_id.id]) or False,
                'ref_base_sign': tax.ref_base_sign,
                'ref_tax_sign': tax.ref_tax_sign,
                'include_base_amount': tax.include_base_amount,
                'description': tax.description,
                'company_id': company_id,
                'type_tax_use': tax.type_tax_use,
                'price_include': tax.price_include
            }
            new_tax = obj_acc_tax.create(cr, uid, vals_tax)
            tax_template_to_tax[tax.id] = new_tax
            # as the accounts have not been created yet, we have to wait before filling these fields
            todo_dict[new_tax] = {
                'account_collected_id': tax.account_collected_id and tax.account_collected_id.id or False,
                'account_paid_id': tax.account_paid_id and tax.account_paid_id.id or False,
            }
            tax_template_ref[tax.id] = new_tax
        # define default values
        ir_values = self.pool.get('ir.values')
        if obj_multi.sale_tax:
            ir_values.set(cr, uid, key='default', key2=False, name="taxes_id", company=obj_multi.company_id.id,
                          models=[('product.product', False)], value=[tax_template_to_tax[obj_multi.sale_tax.id]])
        if obj_multi.purchase_tax:
            ir_values.set(cr, uid, key='default', key2=False, name="supplier_taxes_id", company=obj_multi.company_id.id,
                          models=[('product.product', False)], value=[tax_template_to_tax[obj_multi.purchase_tax.id]])
        return tax_template_ref, todo_dict

    def _create_accounts(self, cr, uid, obj_multi, tax_template_ref, todo_dict, context=None):
        self._logger.info('loading accounts')
        obj_acc_template = self.pool.get('account.account.template')
        obj_acc = self.pool.get('account.account')
        obj_acc_tax = self.pool.get('account.tax')
        acc_template_ref = {}
        obj_acc_root = obj_multi.chart_template_id.account_root_id
        company_id = obj_multi.company_id.id
        # deactivate the parent_store functionnality on account_account for rapidity purpose
        ctx = context and context.copy() or {}
        ctx['defer_parent_store_computation'] = True

        children_acc_template = obj_acc_template.search(cr, uid, [('parent_id', 'child_of', [obj_acc_root.id]),
                                                                  ('nocreate', '!=', True)])
        children_acc_template.sort()
        for account_template in obj_acc_template.browse(cr, uid, children_acc_template, context=context):
            tax_ids = []
            for tax in account_template.tax_ids:
                tax_ids.append(tax_template_ref[tax.id])
            # create the account_account

            dig = obj_multi.code_digits
            code_main = account_template.code and len(account_template.code) or 0
            code_acc = account_template.code or ''
            if code_main > 0 and code_main <= dig and account_template.type != 'view':
                code_acc = str(code_acc) + (str('0' * (dig - code_main)))
            vals = {
                'name': (obj_acc_root.id == account_template.id) and obj_multi.company_id.name or account_template.name,
                'currency_id': account_template.currency_id and account_template.currency_id.id or False,
                'code': code_acc,
                'type': account_template.type,
                'user_type': account_template.user_type and account_template.user_type.id or False,
                'reconcile': account_template.reconcile,
                'shortcut': account_template.shortcut,
                'note': account_template.note,
                'parent_id': account_template.parent_id and ((account_template.parent_id.id in acc_template_ref)
                                                             and acc_template_ref[account_template.parent_id.id]) or False,
                'tax_ids': [(6, 0, tax_ids)],
                'company_id': company_id,
            }
            new_account = obj_acc.create(cr, uid, vals, context=ctx)
            acc_template_ref[account_template.id] = new_account
        # reactivate the parent_store functionnality on account_account
        self.pool.get('account.account')._parent_store_compute(cr)

        for key, value in todo_dict.items():
            if value['account_collected_id'] or value['account_paid_id']:
                obj_acc_tax.write(cr, uid, [key], {
                    'account_collected_id': acc_template_ref.get(value['account_collected_id'], False),
                    'account_paid_id': acc_template_ref.get(value['account_paid_id'], False),
                })
        return acc_template_ref

    def _get_todo_list(self):
        return [
            ('property_account_receivable', 'res.partner', 'account.account'),
            ('property_account_payable', 'res.partner', 'account.account'),
            ('property_account_expense_categ', 'product.category', 'account.account'),
            ('property_account_income_categ', 'product.category', 'account.account'),
            ('property_account_expense', 'product.template', 'account.account'),
            ('property_account_income', 'product.template', 'account.account'),
            ('property_reserve_and_surplus_account', 'res.company', 'account.account')
        ]

    def _create_properties(self, cr, uid, obj_multi, acc_template_ref, context=None):
        self._logger.info('loading properties')
        company_id = obj_multi.company_id.id
        # create the properties
        property_obj = self.pool.get('ir.property')
        fields_obj = self.pool.get('ir.model.fields')

        todo_list = self._get_todo_list()
        for record in todo_list:
            r = []
            r = property_obj.search(cr, uid, [('name', '=', record[0]), ('company_id', '=', company_id)])
            account = getattr(obj_multi.chart_template_id, record[0])
            field = fields_obj.search(cr, uid, [('name', '=', record[0]), ('model', '=', record[1]), ('relation', '=', record[2])])
            vals = {
                'name': record[0],
                'company_id': company_id,
                'fields_id': field[0],
                'value': account and 'account.account,' + str(acc_template_ref[account.id]) or False,
            }

            if r:
                # the property exist: modify it
                property_obj.write(cr, uid, r, vals)
            else:
                # create the property
                property_obj.create(cr, uid, vals)

    def _get_journal_vals(self, cr, uid, journal_tmpl, obj_multi, acc_template_ref, sequence_template_ref, context=None):
        return {
            'name': journal_tmpl.name,
            'code': journal_tmpl.code,
            'type': journal_tmpl.type,
            'refund_journal': journal_tmpl.refund_journal,
            'type_control_ids': [(6, 0, [type_control.id for type_control in journal_tmpl.type_control_ids])],
            'account_control_ids': [(6, 0, [acc_template_ref[account_control.id] for account_control in journal_tmpl.account_control_ids])],
            'view_id': journal_tmpl.view_id.id,
            'default_credit_account_id': acc_template_ref.get(journal_tmpl.default_credit_account_id.id, False),
            'default_debit_account_id': acc_template_ref.get(journal_tmpl.default_debit_account_id.id, False),
            'centralisation': journal_tmpl.centralisation,
            'update_posted': journal_tmpl.update_posted,
            'group_invoice_lines': journal_tmpl.group_invoice_lines,
            'sequence_id': sequence_template_ref[journal_tmpl.sequence_id.id],
            'user_id': journal_tmpl.user_id.id,
            'groups_id': [(6, 0, [group.id for group in journal_tmpl.groups_id])],
            'currency': journal_tmpl.currency.id,
            'entry_posted': journal_tmpl.entry_posted,
            'company_id': obj_multi.company_id.id,
            'allow_date': journal_tmpl.allow_date,
            'analytic_journal_id': journal_tmpl.analytic_journal_id.id if journal_tmpl.analytic_journal_id and
                journal_tmpl.analytic_journal_id.company_id.id in (obj_multi.company_id.id, False) else False,
        }

    def _create_journals(self, cr, uid, obj_multi, tax_template_ref, acc_template_ref, context=None):
        self._logger.info('loading journals')
        jnl_template_ref = {}
        if obj_multi.chart_template_id.journal_ids:
            company_id = obj_multi.company_id.id
            # create sequences
            sequence_template_ref = {}
            sequence_template_ids = set([journal_tmpl.sequence_id.id for journal_tmpl in obj_multi.chart_template_id.journal_ids])
            sequence_obj = self.pool.get('ir.sequence')
            for sequence_tmpl_info in self.pool.get('ir.sequence.template').read(cr, uid, sequence_template_ids, context=context):
                sequence_tmpl_info_id = sequence_tmpl_info['id']
                del sequence_tmpl_info['id']
                sequence_template_ref[sequence_tmpl_info_id] = sequence_obj.create(cr, uid, sequence_tmpl_info, context)
            # create journals
            journal_obj = self.pool.get('account.journal')
            journal_tmpl_ids = [journal_tmpl.id for journal_tmpl in obj_multi.chart_template_id.journal_ids]
            for journal_tmpl in self.pool.get('account.journal.template').browse(cr, uid, journal_tmpl_ids, {'force_company': company_id}):
                journal_vals = self._get_journal_vals(cr, uid, journal_tmpl, obj_multi, acc_template_ref, sequence_template_ref, context)
                jnl_template_ref[journal_tmpl.id] = journal_obj.create(cr, uid, journal_vals, context)
        else:
            self._native_create_journals(cr, uid, obj_multi, tax_template_ref, acc_template_ref, context)
        self._create_bank_journals(cr, uid, obj_multi, tax_template_ref, acc_template_ref, context)
        return jnl_template_ref

    def _native_create_journals(self, cr, uid, obj_multi, tax_template_ref, acc_template_ref, context=None):
        company_id = obj_multi.company_id.id
        obj_data = self.pool.get('ir.model.data')
        obj_sequence = self.pool.get('ir.sequence')
        analytic_journal_obj = self.pool.get('account.analytic.journal')
        obj_journal = self.pool.get('account.journal')
        # Creating Journals Sales and Purchase
        vals_journal = {}
        data_id = obj_data.search(cr, uid, [('model', '=', 'account.journal.view'), ('name', '=', 'account_sp_journal_view')])
        data = obj_data.browse(cr, uid, data_id[0], context=context)
        view_id = data.res_id

        seq_id = obj_sequence.search(cr, uid, [('name', '=', 'Account Journal')])[0]

        if obj_multi.seq_journal:
            seq_id_sale = obj_sequence.search(cr, uid, [('name', '=', 'Sale Journal')])[0]
            seq_id_purchase = obj_sequence.search(cr, uid, [('name', '=', 'Purchase Journal')])[0]
            seq_id_sale_refund = obj_sequence.search(cr, uid, [('name', '=', 'Sales Refund Journal')])
            if seq_id_sale_refund:
                seq_id_sale_refund = seq_id_sale_refund[0]
            seq_id_purchase_refund = obj_sequence.search(cr, uid, [('name', '=', 'Purchase Refund Journal')])
            if seq_id_purchase_refund:
                seq_id_purchase_refund = seq_id_purchase_refund[0]
        else:
            seq_id_sale = seq_id
            seq_id_purchase = seq_id
            seq_id_sale_refund = seq_id
            seq_id_purchase_refund = seq_id

        vals_journal['view_id'] = view_id

        # Sales Journal
        analitical_sale_ids = analytic_journal_obj.search(cr, uid, [('type', '=', 'sale')])
        analitical_journal_sale = analitical_sale_ids and analitical_sale_ids[0] or False

        vals_journal['name'] = _('Sales Journal')
        vals_journal['type'] = 'sale'
        vals_journal['code'] = _('SAJ')
        vals_journal['sequence_id'] = seq_id_sale
        vals_journal['company_id'] = company_id
        vals_journal['analytic_journal_id'] = analitical_journal_sale

        if obj_multi.chart_template_id.property_account_receivable:
            vals_journal['default_credit_account_id'] = acc_template_ref[obj_multi.chart_template_id.property_account_income_categ.id]
            vals_journal['default_debit_account_id'] = acc_template_ref[obj_multi.chart_template_id.property_account_income_categ.id]

        obj_journal.create(cr, uid, vals_journal)

        # Purchase Journal
        analitical_purchase_ids = analytic_journal_obj.search(cr, uid, [('type', '=', 'purchase')])
        analitical_journal_purchase = analitical_purchase_ids and analitical_purchase_ids[0] or False

        vals_journal['name'] = _('Purchase Journal')
        vals_journal['type'] = 'purchase'
        vals_journal['code'] = _('EXJ')
        vals_journal['sequence_id'] = seq_id_purchase
        vals_journal['view_id'] = view_id
        vals_journal['company_id'] = company_id
        vals_journal['analytic_journal_id'] = analitical_journal_purchase

        if obj_multi.chart_template_id.property_account_payable:
            vals_journal['default_credit_account_id'] = acc_template_ref[obj_multi.chart_template_id.property_account_expense_categ.id]
            vals_journal['default_debit_account_id'] = acc_template_ref[obj_multi.chart_template_id.property_account_expense_categ.id]

        obj_journal.create(cr, uid, vals_journal)

        # Creating Journals Sales Refund and Purchase Refund
        vals_journal = {}
        data_id = obj_data.search(cr, uid, [('model', '=', 'account.journal.view'),
                                            ('name', '=', 'account_sp_refund_journal_view')], context=context)
        data = obj_data.browse(cr, uid, data_id[0], context=context)
        view_id = data.res_id

        # Sales Refund Journal
        vals_journal = {
            'view_id': view_id,
            'name': _('Sales Refund Journal'),
            'type': 'sale_refund',
            'refund_journal': True,
            'code': _('SCNJ'),
            'sequence_id': seq_id_sale_refund,
            'analytic_journal_id': analitical_journal_sale,
            'company_id': company_id
        }

        if obj_multi.chart_template_id.property_account_receivable:
            vals_journal['default_credit_account_id'] = acc_template_ref[obj_multi.chart_template_id.property_account_income_categ.id]
            vals_journal['default_debit_account_id'] = acc_template_ref[obj_multi.chart_template_id.property_account_income_categ.id]

        obj_journal.create(cr, uid, vals_journal, context=context)

        # Purchase Refund Journal
        vals_journal = {
            'view_id': view_id,
            'name': _('Purchase Refund Journal'),
            'type': 'purchase_refund',
            'refund_journal': True,
            'code': _('ECNJ'),
            'sequence_id': seq_id_purchase_refund,
            'analytic_journal_id': analitical_journal_purchase,
            'company_id': company_id
        }

        if obj_multi.chart_template_id.property_account_payable:
            vals_journal['default_credit_account_id'] = acc_template_ref[obj_multi.chart_template_id.property_account_expense_categ.id]
            vals_journal['default_debit_account_id'] = acc_template_ref[obj_multi.chart_template_id.property_account_expense_categ.id]

        obj_journal.create(cr, uid, vals_journal, context=context)

    def _create_bank_journals(self, cr, uid, obj_multi, tax_template_ref, acc_template_ref, context=None):
        if not obj_multi.bank_accounts_id:
            return
        company_id = obj_multi.company_id.id
        obj_data = self.pool.get('ir.model.data')
        obj_sequence = self.pool.get('ir.sequence')
        analytic_journal_obj = self.pool.get('account.analytic.journal')
        obj_journal = self.pool.get('account.journal')
        obj_acc = self.pool.get('account.account')
        # Bank Journals
        data_id = obj_data.search(cr, uid, [('model', '=', 'account.journal.view'), ('name', '=', 'account_journal_bank_view')])
        data = obj_data.browse(cr, uid, data_id[0], context=context)
        view_id_cash = data.res_id

        data_id = obj_data.search(cr, uid, [('model', '=', 'account.journal.view'), ('name', '=', 'account_journal_bank_view_multi')])
        data = obj_data.browse(cr, uid, data_id[0], context=context)
        view_id_cur = data.res_id
        ref_acc_bank = obj_multi.chart_template_id.bank_account_view_id
        account_type_ids = self.pool.get('account.account.type').search(cr, uid, [('report_type', '=', 'liability')], limit=1, context=context)

        current_num = 1
        for line in obj_multi.bank_accounts_id:
            # create the account_account for this bank journal
            tmp = line.acc_name
            dig = obj_multi.code_digits
            if ref_acc_bank.code:
                try:
                    new_code = str(int(ref_acc_bank.code.ljust(dig, '0')) + current_num)
                except:
                    new_code = str(ref_acc_bank.code.ljust(dig - len(str(current_num)), '0')) + str(current_num)
            vals = {
                'name': tmp,
                'currency_id': line.currency_id and line.currency_id.id or False,
                'code': new_code,
                'type': 'liquidity',
                'user_type': account_type_ids and account_type_ids[0] or False,
                'reconcile': True,
                'parent_id': acc_template_ref[ref_acc_bank.id] or False,
                'company_id': company_id,
            }
            acc_cash_id = obj_acc.create(cr, uid, vals)

            if obj_multi.seq_journal:
                vals_seq = {
                    'name': _('Bank Journal ') + vals['name'],
                    'code': 'account.journal',
                }
                seq_id = obj_sequence.create(cr, uid, vals_seq)

            # create the bank journal
            analitical_bank_ids = analytic_journal_obj.search(cr, uid, [('type', '=', 'situation')])
            analitical_journal_bank = analitical_bank_ids and analitical_bank_ids[0] or False

            vals_journal = {}
            vals_journal['name'] = vals['name']
            vals_journal['code'] = _('BNK') + str(current_num)
            vals_journal['sequence_id'] = seq_id
            vals_journal['type'] = line.account_type == 'cash' and 'cash' or 'bank'
            vals_journal['company_id'] = company_id
            vals_journal['analytic_journal_id'] = analitical_journal_bank

            if line.currency_id:
                vals_journal['view_id'] = view_id_cur
                vals_journal['currency'] = line.currency_id.id
            else:
                vals_journal['view_id'] = view_id_cash
            vals_journal['default_credit_account_id'] = acc_cash_id
            vals_journal['default_debit_account_id'] = acc_cash_id
            obj_journal.create(cr, uid, vals_journal)
            current_num += 1

    def _get_fiscal_position_vals(self, cr, uid, obj_multi, position, context=None):
        company_id = obj_multi.company_id.id
        return {
            'company_id': company_id,
            'name': position.name,
        }

    def _create_fiscal_position(self, cr, uid, obj_multi, position, tax_template_ref, acc_template_ref, jnl_template_ref, context=None):
        vals_fp = self._get_fiscal_position_vals(cr, uid, obj_multi, position, context)
        new_fp = self.pool.get('account.fiscal.position').create(cr, uid, vals_fp)
        obj_tax_fp = self.pool.get('account.fiscal.position.tax')
        for tax in position.tax_ids:
            vals_tax = {
                'tax_src_id': tax_template_ref[tax.tax_src_id.id],
                'tax_dest_id': tax.tax_dest_id and tax_template_ref[tax.tax_dest_id.id] or False,
                'position_id': new_fp,
            }
            obj_tax_fp.create(cr, uid, vals_tax)
        obj_ac_fp = self.pool.get('account.fiscal.position.account')
        for acc in position.account_ids:
            vals_acc = {
                'account_src_id': acc_template_ref[acc.account_src_id.id],
                'account_dest_id': acc_template_ref[acc.account_dest_id.id],
                'position_id': new_fp,
            }
            obj_ac_fp.create(cr, uid, vals_acc)
        return new_fp

    def _create_fiscal_positions(self, cr, uid, obj_multi, tax_template_ref, acc_template_ref, jnl_template_ref, context=None):
        self._logger.info('loading fiscal positions')
        obj_fiscal_position_template = self.pool.get('account.fiscal.position.template')

        fp_ids = obj_fiscal_position_template.search(cr, uid, [('chart_template_id', '=', obj_multi.chart_template_id.id)])
        if fp_ids:
            for position in obj_fiscal_position_template.browse(cr, uid, fp_ids, context):
                self._create_fiscal_position(cr, uid, obj_multi, position, tax_template_ref, acc_template_ref, jnl_template_ref, context)

    def _configure_accounts_by_resource(self, cr, uid, obj_multi, acc_template_ref, context=None):
        context = context or {}
        context['force_company'] = obj_multi.company_id.id
        self._logger.info('loading accounts by resource')
        for by_resource in obj_multi.chart_template_id.by_resource_ids:
            self.pool.get(by_resource.model_id.model).write(cr, uid, by_resource.res_id,
                                                            {by_resource.field_id.name: acc_template_ref[by_resource.account_id.id]}, context)

    def _create_account_models(self, cr, uid, obj_multi, jnl_template_ref, acc_template_ref, context=None):
        self._logger.info('loading account models')
        company_id = obj_multi.company_id.id
        account_model_obj = self.pool.get('account.model')
        for account_model in obj_multi.chart_template_id.account_model_ids:
            line_vals = []
            for line in account_model.lines_id:
                line_vals.append({
                    'name': line.name,
                    'sequence': line.sequence,
                    'quantity': line.quantity,
                    'debit': line.debit,
                    'credit': line.credit,
                    'account_id': acc_template_ref[line.account_id.id],
                    'analytic_account_id': line.analytic_account_id.id,
                    'amount_currency': line.amount_currency,
                    'currency_id': line.currency_id.id,
                    'partner_id': line.partner_id.id,
                    'date_maturity': line.date_maturity,
                })
            account_model_obj.create(cr, uid, {
                'name': account_model.name,
                'journal_id': jnl_template_ref[account_model.journal_id.id],
                'company_id': company_id,
                'lines_id': [(0, 0, vals) for vals in line_vals],
                'legend': account_model.legend,
            }, context)

    def execute(self, cr, uid, ids, context=None):
        obj_multi = self.browse(cr, uid, ids[0])
        self._logger.info('installing the chart of accounts for %s company: %s' % (obj_multi.company_id.name, obj_multi.chart_template_id.name))
        tax_template_ref, todo_dict = self._create_taxes(cr, uid, obj_multi, context)
        acc_template_ref = self._create_accounts(cr, uid, obj_multi, tax_template_ref, todo_dict, context)
        self._create_properties(cr, uid, obj_multi, acc_template_ref, context)
        jnl_template_ref = self._create_journals(cr, uid, obj_multi, tax_template_ref, acc_template_ref, context)
        self._create_fiscal_positions(cr, uid, obj_multi, tax_template_ref, acc_template_ref, jnl_template_ref, context)
        self._configure_accounts_by_resource(cr, uid, obj_multi, acc_template_ref, context)
        self._create_account_models(cr, uid, obj_multi, jnl_template_ref, acc_template_ref, context)

MultiAccountsChartsWizard()
