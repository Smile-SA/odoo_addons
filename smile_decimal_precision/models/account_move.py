from odoo import api, fields, models, tools
from odoo.tools.misc import formatLang

class AccountTax(models.Model):
    _inherit = 'account.move'
    @api.depends('line_ids.price_subtotal', 'line_ids.tax_base_amount', 'line_ids.tax_line_id', 'partner_id', 'currency_id')
    def _compute_invoice_taxes_by_group(self):
        res = super()._compute_invoice_taxes_by_group()
        for move in self:
            elements = []
            for element in move.amount_by_group:
                    item = list(element)
                    item[3] =   formatLang(self.env,item[1], digits=move.currency_id.display_decimal_places, currency_obj=move.currency_id)
                    item[4] =   formatLang(self.env,item[2], digits=move.currency_id.display_decimal_places, currency_obj=move.currency_id)
                    elements +=[tuple(item)]
            move.amount_by_group = elements
