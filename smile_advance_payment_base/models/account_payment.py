# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_advance_payment = fields.Boolean()
    recovery_ids = fields.One2many(
        'account.payment.recovery', 'payment_id',
        'Recoveries', readonly=True)
    advance_residual = fields.Monetary(compute='_get_advance_residual')

    @api.one
    @api.constrains('is_advance_payment', 'journal_id')
    def _check_is_advance_payment(self):
        if self.is_advance_payment != \
                self.journal_id.is_advance_payment:
            if self.is_advance_payment:
                raise ValidationError(
                    _('Please select an advance payment journal'))
            else:
                raise ValidationError(
                    _('Please don\'t select an advance payment journal'))

    @api.one
    @api.depends('amount', 'recovery_ids.amount')
    def _get_advance_residual(self):
        advance_residual = self.amount
        for recovery in self.recovery_ids:
            if recovery.invoice_id.currency_id != self.currency_id:
                advance_residual -= recovery.invoice_id.currency_id.compute(
                    recovery.amount, self.currency_id)
            else:
                advance_residual -= recovery.amount
        self.advance_residual = advance_residual

    @api.one
    @api.depends('invoice_ids', 'payment_type', 'partner_type', 'partner_id')
    def _compute_destination_account_id(self):
        if self.is_advance_payment and not self._context.get('ignore_advance'):
            if self.partner_type == 'customer':
                if not self.partner_id.property_account_receivable_advance_id:
                    raise UserError(
                        _('Please indicate an account advance receivable '
                          'on this customer'))
                self.destination_account_id = \
                    self.partner_id.property_account_receivable_advance_id.id
            else:
                if not self.partner_id.property_account_payable_advance_id:
                    raise UserError(
                        _('Please indicate an account advance payable '
                          'on this supplier'))
                self.destination_account_id = \
                    self.partner_id.property_account_payable_advance_id.id
        else:
            super(AccountPayment, self)._compute_destination_account_id()

    @api.multi
    def cancel(self):
        """ Forbids cancellation of payments having recoveries.
        """
        if self.filtered('recovery_ids'):
            raise UserError(_("You can't cancel a payment with recoveries."))
        return super(AccountPayment, self).cancel()
