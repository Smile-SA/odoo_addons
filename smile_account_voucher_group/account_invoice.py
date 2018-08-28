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

from openerp.osv import orm, fields
from openerp.tools.translate import _

from res_partner import PAYMENT_TYPES
from tools import _get_exception_message

_logger = logging.getLogger(__package__)


class AccountInvoice(orm.Model):
    _inherit = 'account.invoice'
    _group_unicity_key = ['partner_id', 'partner_bank_id']

    def __init__(self, pool, cr):
        super(AccountInvoice, self).__init__(pool, cr)
        states = self._columns['state'].selection
        if 'progress_paid' not in dict(self._columns['state'].selection):
            states = states[:len(states) - 2] + [('progress_paid', 'Scheduled Payment')] + states[-2:]
        self._columns['state'].selection = states
        self._columns['date_due'].states = {'paid': [('readonly', True)]}
        self._columns['residual']._fnct = AccountInvoice._amount_residual

    def _amount_residual(self, cr, uid, ids, name, args, context=None):
        result = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            result[invoice.id] = invoice.amount_total
            if invoice.move_id:
                for move_line in invoice.move_id.line_id:
                    if move_line.account_id.type in ('receivable', 'payable'):
                        if move_line.reconcile_id:
                            result[invoice.id] = 0.0
                        elif move_line.reconcile_partial_id:
                            if move_line.amount_deduce:
                                result[invoice.id] -= move_line.amount_deduce
                            else:
                                opposite_field = move_line.debit and 'credit' or 'debit'
                                result[invoice.id] -= sum([l.amount_currency or abs(l.debit - l.credit)
                                                           for l in move_line.reconcile_partial_id.line_partial_ids
                                                           if getattr(l, opposite_field)])
        return result

    def _get_invoice_ids_from_partners(self, cr, uid, ids, context=None):
        return self.pool.get('account.invoice').search(cr, uid, [('partner_id', 'in', ids),
                                                                 ('state', 'in', ('draft', 'bap', 'open', 'proforma', 'proforma2'))],
                                                       context=context)

    def _get_invoice_ids_from_payment_modes(self, cr, uid, ids, context=None):
        return self.pool.get('account.invoice').search(cr, uid, [('partner_id.payment_mode_id', 'in', ids),
                                                                 ('state', 'in', ('draft', 'bap', 'open', 'proforma', 'proforma2'))],
                                                       context=context)

    _columns = {
        'payment_type': fields.related('partner_id', 'payment_type', type='selection', selection=PAYMENT_TYPES, string='Payment Type', store={
            'account.invoice': (lambda self, cr, uid, ids, context=None: ids, ['partner_id'], 20),
            'res.partner': (_get_invoice_ids_from_partners, ['payment_type'], 20),
        }, readonly=True),
        'partner_bank_necessary': fields.related('partner_id', 'payment_mode_id', 'partner_bank_necessary', type='boolean', store={
            'account.invoice': (lambda self, cr, uid, ids, context=None: ids, ['partner_id'], 20),
            'res.partner': (_get_invoice_ids_from_partners, ['payment_mode_id'], 20),
            'account.payment.mode': (_get_invoice_ids_from_payment_modes, ['partner_bank_necessary'], 20),
        }, string='Bank Account Necessary', readonly=True),
    }

    def onchange_partner_id(self, cr, uid, ids, type, partner_id, date_invoice=False,
                            payment_term=False, partner_bank_id=False, company_id=False):
        res = super(AccountInvoice, self).onchange_partner_id(cr, uid, ids, type, partner_id,
                                                              date_invoice, payment_term, partner_bank_id, company_id)
        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
            res.setdefault('value', {})['partner_bank_necessary'] = partner.payment_mode_id.partner_bank_necessary
        return res

    def _get_refund_ids_to_deduce(self, cr, uid, partner_id=False, context=None):
        domain = [
            ('type', '=', 'in_refund'),
            ('state', '=', 'progress_paid'),
            ('residual', '!=', 0.0),
        ]
        if partner_id:
            domain.append(('partner_id', '=', partner_id))
        return self.search(cr, uid, domain, context=context)

    def _get_invoice_ids_to_pay(self, cr, uid, partner_id=False, context=None):
        domain = [
            ('type', '=', 'in_invoice'),
            ('state', '=', 'progress_paid'),
            ('payment_type', '=', 'G'),
            ('residual', '!=', 0.0),
            ('date_due', '<=', time.strftime('%Y-%m-%d')),
        ]
        if partner_id:
            domain.append(('partner_id', '=', partner_id))
        return self.search(cr, uid, domain, context=context)

    def _get_unicity_key(self, cr, uid, invoice, context=None):
        return tuple([getattr(invoice, field).id for field in self._group_unicity_key])

    def get_invoices_to_pay(self, cr, uid, context=None):
        groups = {}
        invoice_ids = self._get_invoice_ids_to_pay(cr, uid, context=context)
        for invoice in self.browse(cr, uid, invoice_ids, context):
            key = self._get_unicity_key(cr, uid, invoice, context)
            groups.setdefault(key, []).append(invoice)
        refund_ids = self._get_refund_ids_to_deduce(cr, uid, context=context)
        for refund in self.browse(cr, uid, refund_ids, context):
            key = self._get_unicity_key(cr, uid, refund, context)
            if key in groups:
                groups[key].append(refund)
        return groups

    def _get_amount(self, cr, uid, invoices, context=None):
        amount = 0.0
        for invoice in invoices:
            amount += invoice.residual * (-1.0 if invoice.type == 'in_refund' else 1.0)
        return max(amount, 0.0)

    def _get_payment_vals(self, cr, uid, invoices, context=None):
        context = context or {}
        context['force_company'] = context['company_id'] = invoices[0].company_id.id  # company_id for period, force_company for journal
        voucher_obj = self.pool.get('account.voucher')
        partner = invoices[0].partner_id
        journal = partner.payment_mode_id.journal_id
        if not journal:
            raise orm.except_orm(_('Error'), _('Please indicate a journal for payment mode %s and company %s')
                                 % (partner.payment_mode_id.name, invoices[0].company_id.name))
        vals = {
            'type': 'payment',
            'journal_id': journal.id,
            'company_id': context['force_company'],
            'partner_id': partner.id,
            'account_id': journal.default_credit_account_id.id or journal.default_debit_account_id.id,
            'amount': self._get_amount(cr, uid, invoices, context),
            'payment_type': 'G',
            'payment_mode_id': partner.payment_mode_id.id,
            'partner_bank_necessary': partner.payment_mode_id.partner_bank_necessary,
            'partner_bank_id': invoices[0].partner_bank_id.id,
        }
        line_vals = voucher_obj._get_line_vals_from_invoices(cr, uid, invoices, vals, context)
        if not line_vals:
            return {}
        vals['line_ids'] = [(0, 0, lv) for lv in line_vals]
        return vals

    def generate_grouped_payments(self, cr, uid, context=None):
        context = context or {}
        logger = context.get('logger', _logger)
        voucher_ids = []
        voucher_obj = self.pool.get('account.voucher')
        errors_nb = 0
        for key, invoices in self.get_invoices_to_pay(cr, uid, context).iteritems():
            vals = self._get_payment_vals(cr, uid, invoices, context)
            if vals:
                try:
                    voucher_ids.append(voucher_obj.create(cr, uid, vals, context))
                    logger.info(_('Grouped payment created for the following invoices: %s') % (', '.join([inv.number for inv in invoices]),))
                except Exception, e:
                    errors_nb += 1
                    logger.error(_('Grouped payment creation failed for the following invoices: %s - Error: %s')
                                 % (', '.join([inv.number for inv in invoices]), _get_exception_message(e)))
        logger.info(_('%s grouped payments created; %s errors') % (len(voucher_ids), errors_nb))
        return voucher_obj.execute_end_action(cr, uid, voucher_ids, context)

    def invoice_pay_by_group(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'progress_paid'}, context)

    def invoice_pay_customer(self, cr, uid, ids, context=None):
        res = super(AccountInvoice, self).invoice_pay_customer(cr, uid, ids, context)
        invoice = self.browse(cr, uid, ids[0], context=context)
        res['context'].update({
            'default_payment_type': 'I',
            'default_payment_mode_id': invoice.partner_id.payment_mode_id.id,
            'default_partner_bank_necessary': invoice.partner_id.payment_mode_id.partner_bank_necessary,
        })
        return res

    def set_to_progress_paid(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'progress_paid'}, context)

    def set_to_open(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'open'}, context)
