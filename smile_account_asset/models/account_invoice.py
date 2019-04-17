# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_move_create(self):
        for invoice in self:
            for line in invoice.invoice_line_ids:
                if line.asset_category_id and \
                        line.asset_category_id.asset_creation == 'auto':
                    line.create_assets()
        return super(AccountInvoice, self).action_move_create()

    @api.model
    def line_get_convert(self, line, part):
        res = super(AccountInvoice, self).line_get_convert(line, part)
        res['asset_id'] = line.get('asset_id', False)
        return res

    @api.model
    def invoice_line_move_line_get(self):
        res = super(AccountInvoice, self).invoice_line_move_line_get()
        for line_info in res:
            line_info['asset_id'] = self.invoice_line_ids.filtered(
                lambda line: line.id == line_info['invl_id']).asset_id.id
        return res
