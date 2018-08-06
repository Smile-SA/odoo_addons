# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_advance_payment = fields.Boolean()
    recovery_sequence_id = fields.Many2one(
        'ir.sequence', 'Recovery entry sequence')
