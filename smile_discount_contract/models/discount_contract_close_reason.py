# -*- coding: utf-8 -*-

from odoo import fields, models


class DiscountContractCloseReason(models.Model):
    _name = 'discount.contract.close_reason'
    _description = 'Discount Contract Close Reason'

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
