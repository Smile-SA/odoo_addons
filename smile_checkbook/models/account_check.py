# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountCheck(models.Model):
    _name = 'account.check'
    _description = 'Account Check'
    _rec_name = 'number'
    _order = 'number asc'

    number = fields.Integer(
        'Number', required=True, readonly=True, group_operator=None)
    partner_id = fields.Many2one(
        'res.partner', 'Partner', required=True, readonly=True)
    company_id = fields.Many2one(
        'res.company', 'Company', required=True, readonly=True)
    state = fields.Selection(
        [('available', 'Available'), ('used', 'Used'), ('lost', 'Lost'),
         ('destroyed', 'Destroyed'), ('stolen', 'Stolen')],
        'Status', required=True, readonly=False)

    _sql_constraints = [
        ('uniq_number', 'unique(number, partner_id)',
         'Check number must be unique per partner'),
    ]
