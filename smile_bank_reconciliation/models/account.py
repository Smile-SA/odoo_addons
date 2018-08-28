# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>). All Rights Reserved
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


from datetime import datetime

from openerp import models, fields, api, exceptions
from openerp.tools.translate import _
from openerp.tools import float_is_zero

STATES = [('draft', 'Draft'), ('valid', 'Valid')]


class AccountBankReconciliation(models.Model):
    _name = 'account.bank.reconciliation'

    state = fields.Selection(STATES, string='Status', readonly=True, default='draft', copy=False)
    name = fields.Char(string='Reference', required=True, readonly=True,
                       default=lambda self: self.env['ir.sequence'].get('bank.reconciliation'))
    date = fields.Date(string='Date', required=True, states={'draft': [('readonly', False)]},
                       readonly=True, default=fields.datetime.now())
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, domain=[('type', '=', 'bank')],
                                 readonly=True, states={'draft': [('readonly', False)]})
    account_bank_id = fields.Many2one(related='journal_id.default_debit_account_id', readonly=True, string='Bank account', store=True)
    balance_account = fields.Float(store=True, string='Balance of the account book', readonly=True, compute='_compute_reconcile_balances')
    balance_not_close = fields.Float(store=True, string='Not close balance', readonly=True, compute='_compute_reconcile_balances')
    theoretical_balance = fields.Float(store=True, string='Theoretical statement balance', readonly=True,
                                       compute='_compute_reconcile_balances')
    balance_per_statement = fields.Float(string='Balance per bank statement', states={'draft': [('readonly', False)]}, readonly=True)
    gap = fields.Float(store=True, string='Gap', readonly=True, compute='_compute_reconcile_gap')
    reconciliation_voucher_ids = fields.One2many('account.reconciliation.voucher', 'reconciliation_id', string='Reconciliation voucher',
                                                 readonly=True, states={'draft': [('readonly', False)]})
    reconciliation_gap_ids = fields.One2many('account.reconciliation.gap', 'reconciliation_id', string='Reconciliation gap',
                                             readonly=True, states={'draft': [('readonly', False)]})
    account_move_line_ids = fields.One2many('account.move.line', 'reconciliation_id', string='Move Lines', readonly=True)

    @api.one
    @api.constrains('reconciliation_voucher_ids', 'reconciliation_voucher_ids.account_move_line_ids')
    def _check_account_move_line_duplicata(self):
        res = {}
        move_line_ids = []
        for reconciliation_voucher in self.reconciliation_voucher_ids:
            for move_line in reconciliation_voucher.account_move_line_ids:
                if move_line.id in move_line_ids:
                    raise exceptions.Warning(_('Invalid action!'),
                                             _('Move line [%s] in reconciliation voucher [%s] exists in reconciliation voucher [%s]!')
                                             % (move_line.name, reconciliation_voucher.name, res[str(move_line.id)]))
                else:
                    move_line_ids.append(move_line.id)
                    res.update({str(move_line.id): reconciliation_voucher.name})

    @api.multi
    @api.depends('journal_id', 'date', 'reconciliation_voucher_ids')
    def _compute_reconcile_balances(self):
        reconcile_date = self.date or datetime.now().date()
        acc_id = self.journal_id.default_debit_account_id.id
        ids = isinstance(acc_id, (int, long)) and [acc_id] or acc_id
        balance_account = 0.0
        balance_not_close = 0.0
        if acc_id:
            query = self.env['account.move.line']._query_get()
            self._cr.execute("""SELECT l.id, l.account_id, l.reconciliation_voucher_id, SUM(l.debit-l.credit)
                                FROM account_move_line l
                                WHERE l.account_id in %s AND l.date <= %s
                                AND """ + query + """
                                GROUP BY l.id, l.account_id, l.reconciliation_voucher_id
                             """, (tuple(ids), reconcile_date))
            for reconcile_id, account_id, move_id, balance in self._cr.fetchall():
                balance_account += balance
                if not move_id:
                    balance_not_close += balance
        self.balance_account = -balance_account
        self.balance_not_close = balance_not_close
        self.theoretical_balance = balance_not_close - balance_account

    @api.multi
    @api.depends('theoretical_balance', 'balance_per_statement', 'reconciliation_gap_ids')
    def _compute_reconcile_gap(self):
        total_gap = 0.0
        for gap in self.reconciliation_gap_ids:
            total_gap += gap.amount
        self.gap = self.theoretical_balance + self.balance_per_statement + total_gap

    @api.multi
    def button_validate(self):
        self.ensure_one()
        if self.gap:
            currency_id = self.env.user.company_id.currency_id
            digits_rounding_precision = currency_id.rounding
            if not float_is_zero(self.gap, digits_rounding_precision):
                raise exceptions.Warning(_('Invalid action!'), _('Gap must be 0!'))
        if not self.reconciliation_voucher_ids:
            raise exceptions.Warning(_('Invalid action!'), _('No line in reconciliation voucher!'))
        for reconciliation_voucher in self.reconciliation_voucher_ids:
            if not reconciliation_voucher.account_move_line_ids:
                raise exceptions.Warning(_('Invalid action!'),
                                         _('No account move line in reconciliation voucher %s!') % (reconciliation_voucher.name))
            for move_line in reconciliation_voucher.account_move_line_ids:
                if move_line.state != 'valid':
                    raise exceptions.Warning(_('Invalid action!'),
                                             _('Attention! Account move line [%s] linked to voucher [%s] is not valid, your reconciliation'
                                               + 'can not be validated!') % (move_line.name, reconciliation_voucher.name))
        self.write({'state': 'valid'})
        return True

    @api.multi
    def button_cancel(self):
        self.ensure_one()
        self.write({'state': 'draft'})
        return True


class AccountReconciliationVoucher(models.Model):
    _name = 'account.reconciliation.voucher'

    name = fields.Char(string='Reference', copy=False, required=True,
                       default=lambda self: self.env['ir.sequence'].get('bank.reconciliation.voucher'))
    comment = fields.Char(string='Note', copy=False)
    date = fields.Date(string='Date', required=True, copy=False)
    reconciliation_id = fields.Many2one('account.bank.reconciliation', string='Reconciliation', ondelete='cascade')
    account_move_line_ids = fields.Many2many('account.move.line', string='Moves')
    total_debit = fields.Float(store=True, string='Total debit', readonly=True, compute='_compute_total_debit_credit')
    total_credit = fields.Float(store=True, string='Total credit', readonly=True, compute='_compute_total_debit_credit')

    @api.multi
    @api.depends('account_move_line_ids', 'account_move_line_ids.debit', 'account_move_line_ids.credit')
    def _compute_total_debit_credit(self):
        total_debit = 0.0
        total_credit = 0.0
        for move_line in self.account_move_line_ids:
            total_debit += move_line.debit
            total_credit += move_line.credit
        self.total_debit = total_debit
        self.total_credit = total_credit

    @api.model
    def create(self, values):
        res = super(AccountReconciliationVoucher, self).create(values)
        if res.account_move_line_ids:
            res.account_move_line_ids._update_reconciliation_data(res.reconciliation_id.id,
                                                                  res.id,
                                                                  res.reconciliation_id.date)
        return res

    @api.multi
    def write(self, values):
        for voucher in self:
            if 'account_move_line_ids' in values:
                # To unreconcile:
                unreconcile_ids = [idx for idx in voucher.account_move_line_ids.ids
                                   if idx not in values['account_move_line_ids'][0][2]]
                self.env['account.move.line'].browse(unreconcile_ids)._update_reconciliation_data()
                # To reconcile
                reconcile_ids = [idx for idx in values['account_move_line_ids'][0][2]
                                 if idx not in voucher.account_move_line_ids.ids]
                self.env['account.move.line'].browse(reconcile_ids)._update_reconciliation_data(voucher.reconciliation_id.id,
                                                                                                voucher.id,
                                                                                                voucher.reconciliation_id.date)
        return super(AccountReconciliationVoucher, self).write(values)

    @api.multi
    def unlink(self):
        for reconciliation_voucher in self:
            reconciliation_voucher.account_move_line_ids._update_reconciliation_data()
        return super(AccountReconciliationVoucher, self).unlink()


class AccountReconciliationgap(models.Model):
    _name = 'account.reconciliation.gap'

    name = fields.Char(string='Reference', copy=False, required=True)
    amount = fields.Float(string='Amount', required=True, copy=False)
    reconciliation_id = fields.Many2one('account.bank.reconciliation', string='Reconciliation', ondelete='cascade')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    reconciliation_voucher_id = fields.Many2one('account.reconciliation.voucher', string='Reconciliation voucher',
                                                readonly=True, copy=False)
    reconciliation_voucher_date = fields.Date(string='Reconciliation voucher date', readonly=True, copy=False)
    reconciliation_id = fields.Many2one('account.bank.reconciliation', string='Reconciliation', readonly=True, copy=False)

    @api.multi
    def _update_reconciliation_data(self, reconciliation_id=False, reconciliation_voucher_id=False, reconciliation_voucher_date=False):
        self.write({'reconciliation_id': reconciliation_id,
                    'reconciliation_voucher_id': reconciliation_voucher_id,
                    'reconciliation_voucher_date': reconciliation_voucher_date})
        return True


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    @api.multi
    def _get_not_reconciled_moves(self):
        self.ensure_one()
        return self.env['account.move.line'].search([('journal_id', '=', self.id), ('reconciliation_id', '=', False)])
