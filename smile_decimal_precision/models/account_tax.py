# (C) 2023 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools
from odoo.tools.misc import formatLang

class AccountTax(models.Model):
    _inherit = 'account.tax'
    
    @api.model
    def _prepare_tax_totals(self, base_lines, currency, tax_lines=None):
        res = super()._prepare_tax_totals(base_lines, currency, tax_lines)

        groups = res.get('groups_by_subtotal',{})
        subtotals = res.get('subtotals',{})
        for group in groups:            
                items = groups.get(group)
                for item in items:
                    item.update({'formatted_tax_group_amount':formatLang(self.env, item['tax_group_amount'], digits=currency.display_decimal_places, currency_obj=currency)})
        for subtotal in subtotals:
                subtotal.update({'formatted_amount':formatLang(self.env, subtotal['amount'], digits=currency.display_decimal_places, currency_obj=currency)})

        res.update({'formatted_amount_total':formatLang(self.env, res['amount_total'], digits=currency.display_decimal_places, currency_obj=currency),
                    'formatted_amount_untaxed':formatLang(self.env, res['amount_untaxed'], digits=currency.display_decimal_places, currency_obj=currency)
                   
                   })
        return res
