# -*- coding: utf-8 -*-

from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line.date_planned')
    def _compute_date_planned(self):
        for order in self:
            min_date = False
            for line in order.order_line:
                if line.date_planned and \
                        (not min_date or line.date_planned < min_date):
                    min_date = line.date_planned
            if min_date:
                order.date_planned = min_date
