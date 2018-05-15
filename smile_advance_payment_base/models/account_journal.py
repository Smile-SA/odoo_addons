# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_advance_payment = fields.Boolean()
    recovery_sequence_id = fields.Many2one(
        'ir.sequence', 'Recovery entry sequence')
