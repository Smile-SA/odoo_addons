# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    purchase_id = fields.Many2one(
        'purchase.order', 'Purchase Order',
        domain=[('state', '=', 'purchase')])
