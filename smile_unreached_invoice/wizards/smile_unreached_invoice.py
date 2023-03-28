# Copyright 2023 Smile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SmileUnreachedInvoice(models.TransientModel):
    _name = 'smile.unreached.invoice'
    _inherit = 'smile.account.invoice.generic.wizard.abstract'

    purchase_ids = fields.Many2many(
        'purchase.order',
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        context = self._context
        purchase_ids = (
            context.get('active_ids', '')
            if context.get('active_model', '') == 'purchase.order'
            else False
        )
        if purchase_ids:
            res['purchase_ids'] = purchase_ids
        return res

    def _get_order_lines(self):
        order_lines = self.env['purchase.order.line'].search([
            ('order_id', 'in', self.purchase_ids.ids),
            ('qty_to_invoice', '>', 0),
        ])
        return order_lines
