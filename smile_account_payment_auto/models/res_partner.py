# -*- coding: utf-8 -*-

from odoo import api, fields, models

PAYMENT_MODES = [
    ('I', 'Individual'),
    ('G', 'Grouped'),
]


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _get_default_payment_method_id(self):
        return self.env['account.payment.method'].search(
            [('payment_type', '=', 'outbound')], limit=1).id

    payment_mode = fields.Selection(
        PAYMENT_MODES, 'Payment mode', required=True, default='I')
    payment_method_id = fields.Many2one(
        'account.payment.method', 'Payment method', required=True,
        domain=[('payment_type', '=', 'outbound')],
        default=_get_default_payment_method_id)
    has_payments_in_progress = fields.Boolean(
        compute='_has_payments_in_progress', store=True)

    @api.one
    @api.depends('invoice_ids.state')
    def _has_payments_in_progress(self):
        self.has_payments_in_progress = \
            'progress_paid' in self.mapped('invoice_ids.state')
