# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    @api.multi
    def _get_move_line_vals(
            self, amount, journal_type, analytic_account_id,
            default=None, refund=False):
        if journal_type.endswith('_refund'):
            journal_type = journal_type.replace('_refund', '')
            refund = True
        sign = (journal_type == 'purchase') ^ refund and -1 or 1
        vals_list = []
        for tax_info in self.compute_all(amount)['taxes']:
            if tax_info['amount']:
                vals = (default or {}).copy()
                debit, credit = 0.0, tax_info['amount'] * sign
                if credit < 0.0:
                    debit, credit = abs(credit), abs(debit)
                account_id = tax_info['account_id']
                if refund and tax_info['refund_account_id']:
                    account_id = tax_info['refund_account_id']
                tax = self.browse(tax_info['id'])
                vals.update({
                    'account_id': account_id,
                    'debit': debit,
                    'credit': credit,
                    'tax_line_id': tax.id,
                })
                if tax.include_base_amount:
                    vals['tax_ids'] = [(6, 0, tax.children_tax_ids.ids)]
                if tax.analytic:
                    vals['analytic_account_id'] = analytic_account_id
                vals_list.append(vals)
        return vals_list
