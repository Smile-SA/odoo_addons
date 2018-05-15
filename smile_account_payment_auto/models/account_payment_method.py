# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    partner_bank_required = fields.Boolean('Bank account required')
    bank_journal_ids = fields.Many2many(
        'account.journal', 'account_journal_outbound_payment_method_rel',
        'outbound_payment_method', 'journal_id', 'Bank journals',
        domain=[('type', 'in', ('cash', 'bank'))])
