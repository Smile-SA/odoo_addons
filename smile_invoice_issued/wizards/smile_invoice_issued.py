# Copyright 2023 Smile
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SmileInvoiceIssued(models.TransientModel):
    _name = 'smile.invoice.issued'
    _inherit = "smile.account.invoice.generic.wizard.abstract"

    sale_ids = fields.Many2many(
        'sale.order',
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        context = self._context
        sale_ids = (
            context.get('active_ids', '')
            if context.get('active_model', '') == 'sale.order'
            else False
        )
        if sale_ids:
            res['sale_ids'] = sale_ids
        return res

    def _get_order_lines(self):
        order_lines = self.env['sale.order.line'].search([
            ('order_id', 'in', self.sale_ids.ids),
            ('qty_to_invoice', '>', 0),
        ])
        return order_lines
