# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    advance_payment_ids = fields.One2many(
        'account.payment', 'purchase_id', 'Advance payments',
        ondelete='cascade', copy=False,
        readonly=True, states={'purchase': [('readonly', False)]},
        domain=[('is_advance_payment', '=', True)])
