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

import time

import decimal_precision as dp
from openerp.osv import orm, fields
from openerp.tools.translate import _


class AccountVoucher(orm.Model):
    _inherit = 'account.voucher'

    def _get_advance_residual(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for voucher in self.browse(cr, uid, ids, context):
            res[voucher.id] = voucher.amount - sum([line.amount for line in voucher.advance_payment_line_ids], 0.0)
        return res

    def _get_voucher_ids_from_advance_payment_lines(self, cr, uid, ids, context=None):
        return [line.voucher_id.id for line in self.browse(cr, uid, ids, context)]

    _columns = {
        'is_advance_payment': fields.boolean('Advance Payment'),
        'purchase_order_id': fields.many2one('purchase.order', 'Purchase Order', domain=[('state', '=', 'approved')]),
        'advance_payment_line_ids': fields.one2many('account.voucher.invoice.line', 'voucher_id', 'Invoices'),
        'advance_residual': fields.function(_get_advance_residual, method=True, type='float', digits_compute=dp.get_precision('Account'), store={
            'account.voucher': (lambda self, cr, uid, ids, context=None: ids, ['amount'], 20),
            'account.voucher.invoice.line': (_get_voucher_ids_from_advance_payment_lines, ['voucher_id', 'amount'], 20),
        }, string='Advance Residual'),
        'advance_reference': fields.char('Partner Reference', size=64),
    }

    def _get_default_journal_id(self, cr, uid, context=None):
        journal_ids = self.pool.get('account.journal').search(cr, uid, [('type', 'in', ('bank', 'cash'))], context=context)
        return journal_ids and journal_ids[0] or False

    _defaults = {
        'journal_id': _get_default_journal_id,
    }

    def _check_company(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for voucher in self.browse(cr, uid, ids, context):
            if voucher.journal_id.company_id != voucher.company_id != voucher.account_id.company_id:
                return False
        return True

    def _check_amount(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for voucher in self.browse(cr, uid, ids, context):
            if voucher.is_advance_payment and (not voucher.purchase_order_id
                                               or sum([v.amount for v in voucher.purchase_order_id.advance_payment_ids], 0.0)
                                               > voucher.purchase_order_id.amount_total):
                return False
        return True

    _constraints = [
        (_check_company, _('You cannot create a voucher linked to a company different from the ones of journal and account'),
         ['company_id', 'purchase_order_id', 'journal_id']),
        (_check_amount, _('You cannot create an advance payment with an amount bigger than purchase order amount'),
         ['amount', 'is_advance_payment', 'purchase_order_id']),
    ]

    def copy_data(self, cr, uid, voucher_id, default=None, context=None):
        default = default or {}
        default['advance_payment_line_ids'] = []
        return super(AccountVoucher, self).copy_data(cr, uid, voucher_id, default, context)

    def first_move_line_get(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        move_line_vals = super(AccountVoucher, self).first_move_line_get(cr, uid, voucher_id, move_id, company_currency, current_currency, context)
        voucher = self.browse(cr, uid, voucher_id, context)
        if voucher.is_advance_payment:
            field = voucher.type in ('purchase', 'payment') and 'credit' or 'debit'
            move_line_vals[field] = self.browse(cr, uid, voucher_id, context).amount
        return move_line_vals

    def writeoff_move_line_get(self, cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency, context=None):
        move_line_vals = super(AccountVoucher, self).writeoff_move_line_get(cr, uid, voucher_id, line_total, move_id, name,
                                                                            company_currency, current_currency, context)
        if move_line_vals:
            voucher = self.browse(cr, uid, voucher_id, context)
            if voucher.is_advance_payment:
                field = 'default_%s_account_id' % (voucher.type in ('purchase', 'payment') and 'debit' or 'credit')
                move_line_vals['account_id'] = getattr(self.browse(cr, uid, voucher_id, context).journal_id, field).id
        return move_line_vals

    def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None):
        res = super(AccountVoucher, self).onchange_journal(cr, uid, ids, journal_id, line_ids, tax_id, partner_id,
                                                           date, amount, ttype, company_id, context)
        res = res or {}
        res.setdefault('value', {})['is_advance_payment'] = False
        if journal_id:
            res['value']['is_advance_payment'] = self.pool.get('account.journal').browse(cr, uid, journal_id, context).is_advance_journal
            res['value'].update(self.onchange_is_advance_payment(cr, uid, ids, res['value']['is_advance_payment'], context)['value'])
        return res

    def onchange_amount(self, cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date,
                        payment_rate_currency_id, company_id, context=None):
        res = super(AccountVoucher, self).onchange_amount(cr, uid, ids, amount, rate, partner_id, journal_id,
                                                          currency_id, ttype, date, payment_rate_currency_id, company_id, context)
        if journal_id:
            res['value']['is_advance_payment'] = self.pool.get('account.journal').browse(cr, uid, journal_id, context).is_advance_journal
            res['value'].update(self.onchange_is_advance_payment(cr, uid, ids, res['value']['is_advance_payment'], context)['value'])
        return res

    def onchange_is_advance_payment(self, cr, uid, ids, is_advance_payment, context=None):
        if is_advance_payment:
            return {'value': {'line_cr_ids': [], 'line_dr_ids': []}}
        return {'value': {}}


class AccountVoucherInvoiceLine(orm.Model):
    _name = 'account.voucher.invoice.line'
    _description = 'Advance Payment Line'
    _rec_name = 'amount'

    _columns = {
        'voucher_id': fields.many2one('account.voucher', 'Advance Payment', required=True,
                                      domain=[('is_advance_payment', '=', True)], ondelete="restrict"),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', required=True, ondelete="restrict"),
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
        'move_id': fields.many2one('account.move', 'Journal Entry', readonly=True, ondelete='restrict')
    }

    def _check_amount(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for advance_payment_line in self.browse(cr, uid, ids, context):
            if not advance_payment_line.move_id and advance_payment_line.amount <= 0.0 or advance_payment_line.voucher_id.advance_residual < 0.0:
                return False
        return True

    _constraints = [
        (_check_amount, _('You cannot recover more than advance payment amount nor define a negative amount'), ['amount']),
    ]

    def _reconcile(self, cr, uid, line, context=None):
        def _get_lines_to_reconcile(move_lines, account_id=None, types=None):
            return [l for l in move_lines if (not types or l.account_id.type in types) and (not account_id or l.account_id.id == account_id)]
        line.refresh()
        move = line.move_id
        move_line_obj = self.pool.get('account.move.line')
        # Reconcile "Advance Payments" account
        move_lines = _get_lines_to_reconcile(line.voucher_id.move_id.line_id, types=['other'])
        if move_lines[0].account_id.reconcile:
            move_lines += _get_lines_to_reconcile(move.line_id, account_id=move_lines[0].account_id.id)
            move_line_obj.reconcile_partial(cr, uid, [l.id for l in move_lines], context=context)
        # Reconcile partner account
        move_lines = _get_lines_to_reconcile(line.invoice_id.move_id.line_id, types=['payable', 'receivable'])
        if move_lines[0].account_id.reconcile:
            move_lines += _get_lines_to_reconcile(move.line_id, account_id=move_lines[0].account_id.id)
            move_line_obj.reconcile_partial(cr, uid, [l.id for l in move_lines], context=context)

    def _post(self, cr, uid, line, context=None):
        move_obj = self.pool.get('account.move')
        vals = self._get_move_vals(cr, uid, line, context)
        vals['ref'] = line.invoice_id.number
        vals['line_id'] = [(0, 0, x) for x in self._get_move_lines(cr, uid, line, vals, context)]
        move_id = move_obj.create(cr, uid, vals, context)
        move_obj.post(cr, uid, [move_id], context)
        line.write({'move_id': move_id})
        self._reconcile(cr, uid, line, context)

    def post(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for line in self.browse(cr, uid, ids, context):
            self._post(cr, uid, line, context)
        return True

    def _get_move_vals(self, cr, uid, line, context=None):
        sequence_id = line.voucher_id.journal_id.recovery_sequence_id.id or line.voucher_id.journal_id.sequence_id.id
        return {
            'name': self.pool.get('ir.sequence').next_by_id(cr, uid, sequence_id, context),
            'journal_id': line.voucher_id.journal_id.id,
            'date':  line.invoice_id.date_invoice or time.strftime('%Y-%m-%d'),
            'period_id': line.invoice_id.period_id and line.invoice_id.period_id.id or False,
        }

    def _get_move_lines(self, cr, uid, line, default, context=None):
        vals = default and default.copy() or {}
        vals.update({
            'account_id': line.voucher_id.type in ('purchase', 'payment') and line.voucher_id.partner_id.property_account_payable.id
            or line.voucher_id.partner_id.property_account_receivable.id,
            'partner_id': line.voucher_id.partner_id.id,
            'currency_id': line.voucher_id.currency_id.id,
            'amount_currency': 0.0,  # TODO: manage me
            'quantity': 1.0,
            'debit': line.amount,
            'credit': 0.0,
        })
        counterpart_vals = vals.copy()
        counterpart_vals['account_id'] = line.voucher_id.type in ('purchase', 'payment') and line.voucher_id.journal_id.default_debit_account_id.id \
            or line.voucher_id.journal_id.default_debit_account_id.id
        counterpart_vals['debit'], counterpart_vals['credit'] = counterpart_vals['credit'], counterpart_vals['debit']
        return [vals, counterpart_vals]

    def unlink(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        for line in self.browse(cr, uid, ids, context):
            if line.move_id:
                line.move_id.create_reversals(post_and_reconcile=True)
        return super(AccountVoucherInvoiceLine, self).unlink(cr, uid, ids, context)
