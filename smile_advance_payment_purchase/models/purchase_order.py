# -*- coding: utf-8 -*-

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    advance_payment_ids = fields.One2many(
        'account.payment', 'purchase_id', 'Advance payments',
        ondelete='cascade', copy=False,
        readonly=True, states={'purchase': [('readonly', False)]},
        domain=[('is_advance_payment', '=', True)])
