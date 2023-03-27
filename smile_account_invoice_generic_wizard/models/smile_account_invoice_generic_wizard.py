# Copyright 2023 Smile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import _, fields, models
from odoo.exceptions import AccessError


class SmileAccountInvoiceGenericWizardAbstract(models.AbstractModel):
    _name = 'smile.account.invoice.generic.wizard.abstract'
    _description = 'Generic wizard for account invoice'

    accounting_date = fields.Date(
        string='Accounting date',
        required=True,
    )
    account_credit_id = fields.Many2one(
        'account.account',
        string='Account to credit',
        required=True,
        ondelete='restrict',
    )
    account_debit_id = fields.Many2one(
        'account.account',
        string='Account to debit',
        required=False,
        ondelete='restrict',
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        required=True,
        ondelete='restrict',
    )
    reversal_date = fields.Date(
        string='Reversal date',
        required=True,
    )

    def _action_open_moves(self, action, moves):
        action['domain'] = [('id', 'in', moves)]
        action['context'] = dict(self._context)
        action['context'].pop('search_default_posted', None)
        return action

    def _check_order_lines(self, order_lines):
        if not order_lines:
            if self._is_purchase_order():
                message = _('No purchase order line to invoice.')
            else:
                message = _('No sale order line to invoice.')
            raise AccessError(message)

    def _create_reversal_move(self, account_move):
        move_reversal = self.env['account.move.reversal'].with_context(
            active_model="account.move",
            active_ids=[account_move.id],
        ).create({
            'date_mode': 'custom',
            'date': self.reversal_date,
            'journal_id': self.journal_id.id,
        })
        reversal_move = move_reversal.reverse_moves()
        reversal_move_id = reversal_move['res_id']
        self.env['account.move'].browse(reversal_move_id)

        return [account_move.id, reversal_move_id]

    def _get_expense_account(self, line):
        self.ensure_one()

        if self._is_purchase_order():
            account_id = line.product_id.property_account_expense_id.id
            if not account_id:
                account_id = line.product_id.categ_id.property_account_expense_categ_id.id
        else:
            account_id = line.product_id.property_account_income_id.id
            if not account_id:
                account_id = line.product_id.categ_id.property_account_income_categ_id.id
        return account_id

    def _get_label(self):
        self.ensure_one()

        if self._is_purchase_order():
            label = _('UI')
        else:
            label = _('IE')
        return label

    def _get_line_taxes(self, line):
        self.ensure_one()

        if self._is_purchase_order():
            taxes = line.taxes_id if line.taxes_id else []
        else:
            taxes = line.tax_id if line.tax_id else []
        return taxes

    def _is_purchase_order(self):
        self.ensure_one()
        return self._context.get('active_model', '') == 'purchase.order'

    def _add_credit_and_debit_vals(self, vals, amount):
        self.ensure_one()
        extra_vals = {
            'debit': 0.0,
            'credit': 0.0,
        }
        if self._is_purchase_order():
            extra_vals['debit'] = amount
        else:
            extra_vals['credit'] = amount

        vals.update(extra_vals)
        return vals

    def _process_company_order_lines(self, order_lines, companies):
        self._check_order_lines(order_lines)

        account_move_lines_vals = []
        account_debit_id = self.account_debit_id.id
        grouped_lines = defaultdict(list)
        grouped_taxes = {}
        total_amount = 0
        total_taxes = 0
        label = self._get_label()

        for company in companies:
            for line in order_lines.filtered(lambda order_line: order_line.order_id.company_id == company):
                account_id = self._get_expense_account(line)

                amount = line.qty_to_invoice * line.price_unit
                grouped_lines[account_id].append(amount)

                account_taxes = self._get_line_taxes(line)
                if account_taxes:
                    res = account_taxes.compute_all(amount, product=line.product_id, partner=line.order_id.partner_id)
                    for tax in res['taxes']:
                        total_taxes += tax['amount'] if res['taxes'] else 0
                        account_id = account_debit_id if account_debit_id else tax['account_id']
                        if account_id not in grouped_taxes:
                            grouped_taxes[account_id] = {
                                'tax_line_id': tax['id'],
                                'amount': 0.0,
                            }
                        grouped_taxes[account_id]['amount'] += tax['amount']

            for account_id, amounts in grouped_lines.items():
                amount = sum(amounts)
                total_amount += amount
                account_vals = {
                    'account_id': account_id,
                    'name': _(label),
                }
                account_vals = self._add_credit_and_debit_vals(account_vals, amount)
                account_move_lines_vals.append(account_vals)

            for account_id, tax_info in grouped_taxes.items():
                tax_vals = {
                    'account_id': account_id,
                    'name': _(label),
                    'tax_line_id': tax_info['tax_line_id'],
                }
                tax_vals = self._add_credit_and_debit_vals(tax_vals, tax_info['amount'])
                account_move_lines_vals.append(tax_vals)

            account_amount = {
                'account_id': self.account_credit_id.id,
                'name': _(label),
            }
            if self._is_purchase_order():
                account_amount['credit'] = total_amount + total_taxes
            else:
                account_amount['debit'] = total_amount + total_taxes
            account_move_lines_vals.append(account_amount)

            account_move = self.env['account.move'].create({
                'journal_id': self.journal_id.id,
                'date': self.accounting_date,
                'ref': _(f'{label} - {fields.Datetime.now().date()}'),
                'line_ids': [(0, 0, line_vals) for line_vals in account_move_lines_vals],
                'company_id': company.id,
            })
            account_move.action_post()

            return self._create_reversal_move(account_move)

    def _action_create_moves(self):
        order_lines = self._get_order_lines()
        companies = order_lines.mapped('company_id')
        moves = self._process_company_order_lines(order_lines, companies)
        action = self.env.ref('account.action_move_journal_line').read()[0]
        return self._action_open_moves(action, moves)

    def generate(self):
        self.ensure_one()
        return self._action_create_moves()
