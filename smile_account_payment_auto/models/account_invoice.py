# -*- coding: utf-8 -*-
# (C) 2013 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    partner_bank_required = fields.Boolean(
        related='partner_id.payment_method_id.partner_bank_required',
        readonly=True, store=False)
    partner_bank_id = fields.Many2one(
        states={'draft': [('readonly', False)], 'open': [('readonly', False)]})

    @api.model
    def _setup_fields(self):
        super(AccountInvoice, self)._setup_fields()
        states = self._fields['state'].selection
        if 'progress_paid' not in dict(states):
            states.insert(
                states.index(('paid', 'Paid')),
                ('progress_paid', 'Scheduled Payment'))
        self._fields['state'].selection = states

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        if self.partner_bank_required:
            self.partner_bank_id = self.partner_id.bank_ids and \
                self.partner_id.bank_ids[0]
        return res

    @api.multi
    def set_to_progress_paid(self):
        return self.filtered(lambda inv: inv.state == 'open'). \
            write({'state': 'progress_paid'})

    @api.multi
    def set_to_open(self):
        return self.filtered(lambda inv: inv.state == 'progress_paid'). \
            write({'state': 'open'})

    @api.model
    @api.returns('account.payment', lambda records: records.ids)
    def generate_payments(self):
        payments = self.env['account.payment']
        for invoices in self._get_grouped_invoices_to_pay().values():
            vals = invoices._get_group_payment_vals()
            if vals['amount']:
                payments |= self.env['account.payment'].create(vals)
            else:
                moves_to_reconcile = invoices.mapped('move_id')
                move_lines = moves_to_reconcile.mapped('line_ids')
                for account in move_lines.mapped('account_id'). \
                        filtered('reconcile'):
                    move_lines.filtered(
                        lambda line: line.account_id == account and
                        not line.full_reconcile_id). \
                        auto_reconcile_lines()
                invoices.filtered(
                    lambda inv: not inv.residual).action_invoice_paid()
        payments.post()
        return payments

    @api.model
    def _get_grouped_invoices_to_pay(self):
        """ Payment must be created for invoices that fill these conditions:
        - invoice is in state Scheduled Payment
        - invoice residual is not null
        - due date is lower or equal to today date (not for refund)
        """
        groups = {}
        domain = [
            ('type', 'in', ('in_invoice', 'in_refund')),
            ('state', '=', 'progress_paid'),
            ('residual', '!=', 0.0),
            '|',
            ('date_due', '=', False),  # Refunds
            ('date_due', '<=', fields.Date.today()),
        ]
        for invoice in self.search(domain):
            key = invoice._get_group_payment_key()
            groups.setdefault(key, self.browse())
            groups[key] |= invoice
        return groups

    @api.multi
    def _get_group_payment_key(self):
        self.ensure_one()
        # TODO: fix case of refund: partner bank should not be in the key
        # of refunds, because we want to use refund independently of its bank
        return self.partner_id.id, \
            self.partner_id.payment_mode == 'I' and \
            self.id or self.partner_id.payment_mode, \
            self.partner_id.payment_method_id.id, \
            self.partner_bank_id.id, \
            self.company_id.id

    @api.multi
    def _get_group_payment_vals(self):
        company = self.mapped('company_id')
        payment_method = self.mapped('partner_id.payment_method_id')
        payment_journal = self.env['account.journal'].search([
            ('outbound_payment_method_ids', 'in', payment_method.ids),
            ('company_id', '=', company.id),
        ], limit=1)
        if not payment_journal:
            raise UserError(
                _('Please create a bank journal for the payment method '
                  '%s and the company %s')
                % (payment_method.name, company.name))
        return {
            'invoice_ids': [(6, 0, self.ids)],
            'amount': max(sum(self.mapped('residual_signed')), 0),
            'payment_date': fields.Date.context_today(self),
            'communication':
                ', '.join(x for x in self.mapped('reference') if x),
            'partner_id': self.mapped('partner_id').id,
            'partner_type': 'supplier',
            'journal_id': payment_journal.id,
            'payment_type': payment_method.payment_type,
            'payment_method_id': payment_method.id,
            'payment_mode': self.mapped('partner_id').payment_mode,
        }
