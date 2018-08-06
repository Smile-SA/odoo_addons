# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.model
    def _get_default_product_uom(self):
        return self.env.ref('product.product_uom_unit').id

    date_planned = fields.Datetime(required=False)
    product_id = fields.Many2one(required=False)
    product_uom = fields.Many2one(default=_get_default_product_uom)
