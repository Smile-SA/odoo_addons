# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _get_advance_payments(self):
        advance_payments = super(AccountInvoice, self). \
            _get_advance_payments()
        advance_payments |= self.env['account.payment'].search([
            ('purchase_id.order_line.invoice_lines.invoice_id',
             '=', self.id),
        ])
        return advance_payments
