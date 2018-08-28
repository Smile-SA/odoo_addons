# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
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

from openerp import netsvc
from openerp.osv import orm, fields
from openerp.tools.translate import _

from res_partner import PAYMENT_TYPES
from tools import _get_exception_message

_logger = logging.getLogger(__package__)


class AccountVoucher(orm.Model):
    _inherit = 'account.voucher'

    _columns = {
        'payment_type': fields.selection(PAYMENT_TYPES, 'Payment Type', required=True),
        'payment_mode_id': fields.many2one("account.payment.mode", 'Payment Mode', required=True),
        'partner_bank_necessary': fields.related('payment_mode_id', 'partner_bank_necessary', type='boolean', store={
            'account.voucher': (lambda self, cr, uid, ids, context=None: ids, ['payment_mode_id'], 10),
        }, string='Bank Account Necessary', readonly=True),
        'partner_bank_id': fields.many2one('res.partner.bank', 'Bank Account'),
    }

    def _get_default_payment_mode_id(self, cr, uid, context=None):
        mode_ids = self.pool.get('account.payment.mode').search(cr, uid, [], limit=1, context=context)
        return mode_ids and mode_ids[0] or False

    _defaults = {
        'payment_type': 'I',
        'payment_mode_id': _get_default_payment_mode_id,
    }

    def execute_end_action(self, cr, uid, ids, context=None):
        context = context or {}
        logger = context.get('logger', _logger)
        wkf_service = netsvc.LocalService('workflow')
        if isinstance(ids, (int, long)):
            ids = [ids]
        for voucher_id in ids:
            try:
                wkf_service.trg_validate(uid, 'account.voucher', voucher_id, 'proforma_voucher', cr)
                logger.info(_('Grouped payment [id=%s] confirmed with success') % (voucher_id,))
            except Exception, e:
                logger.error(_('Grouped payment [id=%s] confirmation failed: %s - Error: %s')
                             % (voucher_id, _get_exception_message(e)))
        return True

    def _get_line_vals_from_invoices(self, cr, uid, invoices, voucher_vals, context=None):
        context = context or {}
        invoice_residual_by_move_line_id = {}
        context['move_line_ids'] = []
        for invoice in invoices:
            for move_line in invoice.move_id.line_id:
                if move_line.account_id.type == 'payable' and move_line.state == 'valid' and not move_line.reconcile_id:
                    context['move_line_ids'].append(move_line.id)
                    invoice_residual_by_move_line_id[move_line.id] = invoice.residual
        res = self.recompute_voucher_lines(cr, uid, None, voucher_vals['partner_id'], voucher_vals['journal_id'],
                                           voucher_vals['amount'], False, 'payment', time.strftime('%Y-%m-%d'), context)
        line_vals = res['value']['line_dr_ids'] + res['value']['line_cr_ids']
        for index, lv in enumerate(line_vals):
            if lv['move_line_id'] not in context['move_line_ids']:
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

    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=None):
        res = super(AccountVoucher, self).onchange_partner_id(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context)
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context)
            partner_bank_necessary = partner.payment_mode_id.partner_bank_necessary
            partner_bank_id = False
            if partner_bank_necessary:
                if ttype in ('purchase', 'payment'):
                    partner_bank_id = len(partner.bank_ids) == 1 and partner.bank_ids[0].id or False
                elif journal_id:
                    company = self.pool.get('account.journal').browse(cr, uid, journal_id, context).company_id
                    partner_bank_id = len(company.partner_id.bank_ids) == 1 and company.partner_id.bank_ids[0].id or False
            res.setdefault('value', {}).update({'payment_type': partner.payment_type,
                                                'payment_mode_id': partner.payment_mode_id.id,
                                                'partner_bank_necessary': partner_bank_necessary,
                                                'partner_bank_id': partner_bank_id})
        return res

    def proforma_voucher(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        voucher_ids_to_reconcile = []
        move_line_obj = self.pool.get('account.move.line')
        for voucher in self.browse(cr, uid, ids, context):
            if not voucher.amount and not voucher.writeoff_amount and sum([line.amount for line in voucher.line_ids]):
                voucher.write({'state': 'posted'})
                move_line_ids_to_reconcile = []
                voucher_ids_to_reconcile.append(voucher.id)
                for line in voucher.line_ids:
                    if line.amount:
                        amount_deduce = line.move_line_id.amount_deduce + line.amount
                        line.move_line_id.write({'amount_deduce': amount_deduce})
                        move_line_ids_to_reconcile.append(line.move_line_id.id)
                move_line_obj.reconcile_partial(cr, uid, move_line_ids_to_reconcile, context=context)
        wkf_service = netsvc.LocalService('workflow')
        for voucher in self.browse(cr, uid, voucher_ids_to_reconcile, context):
            for line in voucher.line_ids:
                if line.invoice_id and not line.invoice_id.residual:
                    wkf_service.trg_validate(uid, 'account.invoice', line.invoice_id.id, 'force_invoice_paid', cr)
        return super(AccountVoucher, self).proforma_voucher(cr, uid, list(set(ids) - set(voucher_ids_to_reconcile)), context)

    def recompute_voucher_lines(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
        res = super(AccountVoucher, self).recompute_voucher_lines(cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context)
        context = context or {}
        if context.get('invoice_id') and res.get('value', {}).get('line_cr_ids'):
            invoice_obj = self.pool.get('account.invoice')
            invoice = invoice_obj.browse(cr, uid, context['invoice_id'], context)
            if invoice.type in ('in_refund', 'out_refund'):
                return res
            move_line_ids = [line.id for line in invoice.move_id.line_id]
            for index, vals in enumerate(res.get('value', {}).get('line_dr_ids')):
                if vals['move_line_id'] in move_line_ids:
                    vals['amount'] = invoice.residual
                else:
                    vals['amount'] = 0.0
            amount_to_deduce = invoice.residual
            refund_by_move_line_id = {}
            refund_ids = invoice_obj._get_refund_ids_to_deduce(cr, uid, invoice.partner_id.id, context)
            for refund in invoice_obj.browse(cr, uid, refund_ids, context):
                for line in refund.move_id.line_id:
                    if line.account_id.type in ('receivable', 'payable'):
                        refund_by_move_line_id[line.id] = refund
            for index, vals in enumerate(res.get('value', {}).get('line_cr_ids')):
                if vals['move_line_id'] in refund_by_move_line_id:
                    vals['amount'] = min(amount_to_deduce, refund_by_move_line_id[vals['move_line_id']].residual)
                    res['value']['line_cr_ids'][index] = vals
                    amount_to_deduce -= vals['amount']
                else:
                    vals['amount'] = 0.0
            res['value']['amount'] = sum([l['amount'] * (l['type'] == 'cr' and -1.0 or 1.0)
                                          for l in res['value']['line_dr_ids'] + res['value']['line_cr_ids']])
        return res

    def cancel_voucher(self, cr, uid, ids, context=None):
        res = super(AccountVoucher, self).cancel_voucher(cr, uid, ids, context)
        if isinstance(ids, (int, long)):
            ids = [ids]
        reconcile_obj = self.pool.get('account.move.reconcile')
        for voucher in self.browse(cr, uid, ids, context):
            if not voucher.amount:
                for vline in voucher.line_ids:
                    if vline.invoice_id:
                        for mline in vline.invoice_id.move_id.line_id:
                            reconcile_id = mline.reconcile_id.id or mline.reconcile_partial_id.id
                            if reconcile_id:
                                reconcile_obj.unlink(cr, uid, reconcile_id, context)
                                break
        return res


class AccountVoucherLine(orm.Model):
    _inherit = 'account.voucher.line'

    def _get_invoice_ids(self, cr, uid, ids, name, arg, context=None):
        move_ids_by_line = dict([(avl.id, avl.move_line_id and avl.move_line_id.move_id.id or False) for avl in self.browse(cr, uid, ids, context)])
        invoice_obj = self.pool.get('account.invoice')
        invoice_ids = invoice_obj.search(cr, uid, [('move_id', 'in', move_ids_by_line.values())], context=context)
        invoice_ids_by_move = dict([(inv.move_id.id, inv.id) for inv in invoice_obj.browse(cr, uid, invoice_ids, context)])
        return dict([(move_line_id, invoice_ids_by_move.get(move_id, False)) for move_line_id, move_id in move_ids_by_line.iteritems()])

    _columns = {
        'invoice_id': fields.function(_get_invoice_ids, method=True, type='many2one', relation='account.invoice', string="Invoice", store={
            'account.voucher.line': (lambda self, cr, uid, ids, context=None: ids, ['move_line_id'], 5),
        }),
    }
