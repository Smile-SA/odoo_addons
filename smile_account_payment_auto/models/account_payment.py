# -*- coding: utf-8 -*-
# (C) 2013 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from .res_partner import PAYMENT_MODES


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    payment_mode = fields.Selection(
        PAYMENT_MODES, required=True, default='I')
    partner_bank_required = fields.Boolean(
        related='payment_method_id.partner_bank_required',
    )
    partner_bank_id = fields.Many2one(
        'res.partner.bank', 'Bank Account', readonly=True,
        states={'draft': [('readonly', False)]})

    @api.onchange('partner_id', 'payment_method_id')
    def _onchange_partner_and_payment_method(self):
        self.payment_mode = self.partner_id.payment_mode
        self.payment_method_id = self.partner_id.payment_method_id
        if self.partner_bank_required:
            self.partner_bank_id = self.partner_id.bank_ids and \
                self.partner_id.bank_ids[0]

    @api.one
    @api.constrains('partner_bank_required', 'partner_bank_id')
    def _check_partner_bank(self):
        if self.partner_bank_required and not self.partner_bank_id:
            raise ValidationError(_('Bank account is required'))

    @api.multi
    def post(self):
        progress_paid_invoices = self.mapped('invoice_ids').filtered(
            lambda inv: inv.state == 'progress_paid')
        progress_paid_invoices.write({'state': 'open'})
        res = super(AccountPayment, self).post()
        progress_paid_invoices.filtered(lambda inv: inv.state == 'open').write(
            {'state': 'progress_paid'})
        return res
