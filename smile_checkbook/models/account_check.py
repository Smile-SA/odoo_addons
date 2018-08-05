# -*- encoding: utf-8 -*-
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

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
        'State', required=True, readonly=False)

    _sql_constraints = [
        ('uniq_number', 'unique(number, partner_id)', 'Check number must be unique per partner'),
    ]
