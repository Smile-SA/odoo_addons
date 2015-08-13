# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
import time

from openerp import models, api
from openerp import fields
from openerp.tools.translate import _

from res_partner import PAYMENT_TYPES
from tools import _get_exception_message

_logger = logging.getLogger(__package__)


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    @api.model
    def _get_default_payment_method(self):
        modes = self.env['account.payment.method'].search([], limit=1)
        return modes or False

    payment_type = fields.Selection(PAYMENT_TYPES, string='Payment Type', required=True, default='I')
    payment_method_id = fields.Many2one("account.payment.method", string='Payment Mode', required=True, default=_get_default_payment_method)
    partner_bank_necessary = fields.Boolean(related='payment_method_id.partner_bank_necessary',
                                            string='Bank Account Necessary', readonly=True)
    partner_bank_id = fields.Many2one('res.partner.bank', string='Bank Account')

    @api.multi
    def execute_end_action(self):
        logger = self._context.get('logger', _logger)
        for voucher in self:
            try:
                voucher.signal_workflow('proforma_voucher')
                logger.info(_('Grouped payment [id=%s] confirmed with success') % (voucher.id,))
            except Exception, e:
                logger.error(_('Grouped payment [id=%s] confirmation failed: %s - Error: %s')
                             % (voucher.id, voucher.id, _get_exception_message(e)))
        return True

    @api.model
    def _get_line_vals_from_invoices(self, invoices, voucher_vals):
        invoice_residual_by_move_line_id = {}
        self = self.with_context(move_line_ids=[])
        for invoice in invoices:
            for move_line in invoice.move_id.line_id:
                if move_line.account_id.type == 'payable' and move_line.state == 'valid' and not move_line.reconcile_id:
                    self._context['move_line_ids'].append(move_line.id)
                    invoice_residual_by_move_line_id[move_line.id] = invoice.residual
        res = self.recompute_voucher_lines(voucher_vals['partner_id'], voucher_vals['journal_id'],
                                           voucher_vals['amount'], False, 'payment', time.strftime('%Y-%m-%d'))
        line_vals = res['value']['line_dr_ids'] + res['value']['line_cr_ids']
        for index, lv in enumerate(line_vals):
            if lv['move_line_id'] not in self._context['move_line_ids']:
                del line_vals[index]
        for lv in line_vals:
            lv['amount'] = invoice_residual_by_move_line_id[lv['move_line_id']]
        amount = sum([lv['amount'] * (lv['type'] == 'cr' and -1.0 or 1.0) for lv in line_vals], 0.0)
        if amount < 0.0:
            amount_to_pay_before_deduction = sum([lv['amount'] for lv in line_vals if lv['type'] == 'dr'], 0.0)
            if not amount_to_pay_before_deduction:
                return []
            for index, lv in enumerate(line_vals):
                if lv['type'] == 'cr':
                    if amount_to_pay_before_deduction < lv['amount']:
                        lv['amount'] = amount_to_pay_before_deduction
                        lv['reconcile'] = False
                        line_vals[index] = lv
                    amount_to_pay_before_deduction -= lv['amount']
        return line_vals

    @api.multi
    def onchange_partner_id(self, partner_id, journal_id, amount, currency_id, ttype, date):
        res = super(AccountVoucher, self).onchange_partner_id(partner_id, journal_id, amount, currency_id, ttype, date)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            if ttype in ('purchase', 'payment'):
                partner_bank_necessary = partner.payment_method_suppliers_id.partner_bank_necessary
                payment_method_id = partner.payment_method_suppliers_id.id
            else:
                partner_bank_necessary = partner.payment_method_customer_id.partner_bank_necessary
                payment_method_id = partner.payment_method_customer_id.id
            partner_bank_id = False
            if partner_bank_necessary:
                if ttype in ('purchase', 'payment'):
                    partner_bank_id = len(partner.bank_ids) == 1 and partner.bank_ids[0].id or False
                elif journal_id:
                    company = self.env['account.journal'].browse(journal_id).company_id
                    partner_bank_id = len(company.partner_id.bank_ids) == 1 and company.partner_id.bank_ids[0].id or False
            res.setdefault('value', {}).update({'payment_type': partner.payment_type,
                                                'payment_method_id': payment_method_id,
                                                'partner_bank_necessary': partner_bank_necessary,
                                                'partner_bank_id': partner_bank_id})
        return res

    @api.multi
    def proforma_voucher(self):
        voucher_ids_to_reconcile = []
        move_line_obj = self.env['account.move.line']
        for voucher in self:
            if not voucher.amount and not voucher.writeoff_amount and sum([line.amount for line in voucher.line_ids]):
                voucher.write({'state': 'posted'})
                move_line_ids_to_reconcile = []
                voucher_ids_to_reconcile.append(voucher.id)
                for line in voucher.line_ids:
                    if line.amount:
                        amount_deduce = line.move_line_id.amount_deduce + line.amount
                        line.move_line_id.write({'amount_deduce': amount_deduce})
                        move_line_ids_to_reconcile.append(line.move_line_id.id)
                if move_line_ids_to_reconcile:
                    move_line_obj.browse(move_line_ids_to_reconcile).reconcile_partial()

        for voucher in self:
            for line in voucher.line_ids:
                if line.invoice_id and not line.invoice_id.residual:
                    line.invoice_id.signal_workflow('force_invoice_paid')
        vouchers = self.browse(list(set(self._ids) - set(voucher_ids_to_reconcile)))
        return super(AccountVoucher, vouchers).proforma_voucher()

#     @api.multi
#     def recompute_voucher_lines(self, partner_id, journal_id, price, currency_id, ttype, date):
#         res = super(AccountVoucher, self).recompute_voucher_lines(partner_id, journal_id, price, currency_id, ttype, date)
#         if self._context.get('invoice_id') and res.get('value', {}).get('line_cr_ids'):
#             invoice_obj = self.env['account.invoice']
#             invoice = invoice_obj.browse(self._context['invoice_id'])
#             if invoice.type in ('in_refund', 'out_refund'):
#                 return res
#             move_line_ids = [line.id for line in invoice.move_id.line_id]
#             for index, vals in enumerate(res.get('value', {}).get('line_dr_ids')):
#                 if vals['move_line_id'] in move_line_ids:
#                     vals['amount'] = invoice.residual
#                 else:
#                     vals['amount'] = 0.0
#             amount_to_deduce = invoice.residual
#             refund_by_move_line_id = {}
#             refund_ids = invoice_obj._get_refund_ids_to_deduce(invoice.partner_id.id)
#             for refund in refund_ids:
#                 for line in refund.move_id.line_id:
#                     if line.account_id.type in ('receivable', 'payable'):
#                         refund_by_move_line_id[line.id] = refund
#             for index, vals in enumerate(res.get('value', {}).get('line_cr_ids')):
#                 if vals['move_line_id'] in refund_by_move_line_id:
#                     vals['amount'] = min(amount_to_deduce, refund_by_move_line_id[vals['move_line_id']].residual)
#                     res['value']['line_cr_ids'][index] = vals
#                     amount_to_deduce -= vals['amount']
#                 else:
#                     vals['amount'] = 0.0
#             res['value']['amount'] = sum([l['amount'] * (l['type'] == 'cr' and -1.0 or 1.0)
#                                           for l in res['value']['line_dr_ids'] + res['value']['line_cr_ids']])
#         return res

    @api.multi
    def cancel_voucher(self):
        res = super(AccountVoucher, self).cancel_voucher()
        reconcile_obj = self.env['account.move.reconcile']
        for voucher in self:
            if not voucher.amount:
                for vline in voucher.line_ids:
                    if vline.invoice_id:
                        for mline in vline.invoice_id.move_id.line_id:
                            reconcile_id = mline.reconcile_id.id or mline.reconcile_partial_id.id
                            if reconcile_id:
                                reconcile_obj.unlink(reconcile_id)
                                break
        return res


class AccountVoucherLine(models.Model):
    _inherit = 'account.voucher.line'

    invoice_id = fields.Many2one('account.invoice', string="Invoice", compute='_get_invoice', store=True)

    @api.multi
    @api.depends('move_line_id')
    def _get_invoice(self):
        for voucher_line in self:
            voucher_line.invoice_id = voucher_line.move_line_id.invoice.id or False
