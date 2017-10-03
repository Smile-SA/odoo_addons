# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    discount_contract_id = fields.Many2one('discount.contract',
                                           'Discount contract', readonly=True)

    @api.multi
    def view_discount_contract_lines(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'discount.contract.line',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('contract_id', '=', self.discount_contract_id.id)],
            'target': 'new',
        }
