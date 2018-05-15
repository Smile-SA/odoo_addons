# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountPaymentRecovery(models.Model):
    _name = 'account.payment.recovery'
    _description = 'Advance payment recovery'

    payment_id = fields.Many2one(
        'account.payment', 'Advance payment',
        required=True, ondelete='cascade', readonly=True,
        domain=[('is_advance_payment', '=', True)])
    invoice_id = fields.Many2one(
        'account.invoice', 'Invoice', required=True, readonly=True)
    amount = fields.Monetary(
        'Recovered amount', required=True, readonly=True)
    company_id = fields.Many2one(
        related='invoice_id.company_id', readonly=True)
    currency_id = fields.Many2one(
        related='company_id.currency_id', readonly=True)
    move_id = fields.Many2one(
        'account.move', 'Journal entry', readonly=True)

    @api.one
    @api.constrains('payment_id', 'amount')
    def _check_amount(self):
        if self.amount <= 0:
            raise ValidationError(
                _('You cannot recover a negative amount.'))
        if self.payment_id.advance_residual < 0:
            raise ValidationError(
                _('You cannot recover more than the advance payment amount.'))

    @api.multi
    def post(self):
        for recovery in self:
            vals = recovery._get_move_vals()
            recovery.move_id = self.env['account.move'].create(vals)
            for type_ in ('counterpart', 'advance'):
                vals = getattr(recovery, '_get_%s_move_line_vals' % type_)()
                vals['move_id'] = recovery.move_id.id
                self.env['account.move.line'].create(vals)
            recovery.move_id.post()
            moves_to_reconcile = recovery.move_id | recovery.payment_id.move_id
            moves_to_reconcile.mapped('line_ids').auto_reconcile_lines()
        return True

    @api.multi
    def _get_move_vals(self):
        self.ensure_one()
        date = self.invoice_id.date_invoice
        payment_journal = self.payment_id.journal_id
        return {
            'name': payment_journal.recovery_sequence_id.
            with_context(ir_sequence_date=date).next_by_id(),
            'journal_id': payment_journal.id,
            'date': date,
            'ref': self.payment_id.communication or '',
        }

    @api.multi
    def _get_shared_move_line_vals(self):
        self.ensure_one()
        return {
            'partner_id': self.invoice_id.move_id.partner_id.id,
            'invoice_id': self.invoice_id.id,
            'payment_id': self.payment_id.id,
        }

    @api.multi
    def _get_counterpart_move_line_vals(self):
        vals = self._get_shared_move_line_vals()
        amount = self.amount
        from_currency = self.currency_id.with_context(
            date=self.invoice_id.date_invoice)
        to_currency = self.company_id.currency_id
        if from_currency != to_currency:
            vals['currency_id'] = self.currency_id.id
            vals['amount_currency'] = amount
            amount = from_currency.compute(amount, to_currency)
        if self.payment_id.payment_type == 'inbound':
            vals['credit'] = amount
        else:
            vals['debit'] = amount
        partner = self.invoice_id.move_id.partner_id
        if self.payment_id.partner_type == 'customer':
            vals['account_id'] = partner.property_account_receivable_id.id
        else:
            vals['account_id'] = partner.property_account_payable_id.id
        return vals

    @api.multi
    def _get_advance_move_line_vals(self):
        vals = self._get_counterpart_move_line_vals()
        vals['debit'], vals['credit'] = vals['credit'], vals['debit']
        partner = self.invoice_id.move_id.partner_id
        if self.payment_id.partner_type == 'customer':
            if not partner.property_account_receivable_advance_id:
                raise UserError(
                    _('Please indicate an account advance receivable '
                        'on this customer'))
            vals['account_id'] = \
                partner.property_account_receivable_advance_id.id
        else:
            if not partner.property_account_payable_advance_id:
                raise UserError(
                    _('Please indicate an account advance payable '
                        'on this supplier'))
            vals['account_id'] = \
                partner.property_account_payable_advance_id.id
        return vals
