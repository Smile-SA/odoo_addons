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

from openerp import models, api, fields, exceptions
from openerp.tools.translate import _

from res_partner import PAYMENT_TYPES
from tools import _get_exception_message

_logger = logging.getLogger(__package__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    _group_unicity_key = ['partner_id', 'partner_bank_id']

    @api.model
    def _setup_fields(self):
        super(AccountInvoice, self)._setup_fields()
        states = self._fields['state'].selection
        if 'progress_paid' not in dict(self._fields['state'].selection):
            states = states[:len(states) - 2] + [('progress_paid', 'Scheduled Payment')] + states[-2:]
        self._fields['state'].selection = states
#        self._fields['date_due'].states = {'paid': [('readonly', True)]}
        self._fields['residual']._fnct = AccountInvoice._amount_residual

    payment_type = fields.Selection(selection=PAYMENT_TYPES, string='Payment Type', compute='_get_payment_setting', store=True, copy=False)
    partner_bank_necessary = fields.Boolean(string='Bank Account Necessary', readonly=True,
                                            compute='_get_payment_setting', store=True, copy=False)

    @api.multi
    @api.depends('partner_id', 'partner_id.payment_type', 'partner_id.payment_method_suppliers_id',
                 'partner_id.payment_method_suppliers_id.partner_bank_necessary', 'partner_id.payment_method_customer_id',
                 'partner_id.payment_method_customer_id.partner_bank_necessary')
    def _get_payment_setting(self):
        for invoice in self:
            if invoice.type in ('out_invoice', 'out_refund'):
                invoice.partner_bank_necessary = invoice.partner_id.payment_method_customer_id.partner_bank_necessary
            elif invoice.type in ('in_invoice', 'in_refund'):
                invoice.partner_bank_necessary = invoice.partner_id.payment_method_suppliers_id.partner_bank_necessary
            invoice.payment_type = invoice.partner_id.payment_type

    @api.multi
    @api.depends('move_id')
    def _amount_residual(self):
        for invoice in self:
            residual = invoice.amount_total
            if invoice.move_id:
                for move_line in invoice.move_id.line_id:
                    if move_line.account_id.type in ('receivable', 'payable'):
                        if move_line.reconcile_id:
                            residual = 0.0
                        elif move_line.reconcile_partial_id:
                            if move_line.amount_deduce:
                                residual -= move_line.amount_deduce
                            else:
                                opposite_field = move_line.debit and 'credit' or 'debit'
                                residual -= sum([l.amount_currency or abs(l.debit - l.credit)
                                                 for l in move_line.reconcile_partial_id.line_partial_ids
                                                 if getattr(l, opposite_field)])
            invoice.residual = residual

    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        res = super(AccountInvoice, self).onchange_partner_id(type, partner_id, date_invoice, payment_term, partner_bank_id, company_id)
        if partner_id:
            partner = self.env['res.partner'].search([('id', '=', partner_id)])
            if self.type in ('out_invoice', 'out_refund'):
                res.setdefault('value', {})['partner_bank_necessary'] = partner.payment_method_customer_id.partner_bank_necessary
            elif self.type in ('in_invoice', 'in_refund'):
                res.setdefault('value', {})['partner_bank_necessary'] = partner.payment_method_suppliers_id.partner_bank_necessary

        return res

    @api.model
    def _get_refund_ids_to_deduce(self, partner_id=False):
        domain = [
            ('type', '=', 'in_refund'),
            ('state', '=', 'progress_paid'),
            ('residual', '!=', 0.0),
        ]
        if partner_id:
            domain.append(('partner_id', '=', partner_id))
        return self.search(domain)

    @api.model
    def _get_invoice_ids_to_pay(self, partner_id=False):
        domain = [
            ('type', '=', 'in_invoice'),
            ('state', '=', 'progress_paid'),
            ('payment_type', '=', 'G'),
            ('residual', '!=', 0.0),
            ('date_due', '<=', time.strftime('%Y-%m-%d')),
        ]
        if partner_id:
            domain.append(('partner_id', '=', partner_id))
        return self.search(domain)

    @api.model
    def _get_unicity_key(self, invoice):
        return tuple([getattr(invoice, field).id for field in self._group_unicity_key])

    @api.model
    def get_invoices_to_pay(self):
        groups = {}
        for invoice in self._get_invoice_ids_to_pay():
            key = self._get_unicity_key(invoice)
            groups.setdefault(key, []).append(invoice)
        for refund in self._get_refund_ids_to_deduce():
            key = self._get_unicity_key(refund)
            if key in groups:
                groups[key].append(refund)
        return groups

    @api.model
    def _get_amount(self, invoices):
        amount = 0.0
        for invoice in invoices:
            amount += invoice.residual * (-1.0 if invoice.type == 'in_refund' else 1.0)
        return max(amount, 0.0)

    @api.model
    def _get_payment_vals(self, invoices):
        company_id = invoices[0].company_id.id
        self = self.with_context(force_company=company_id, company_id=company_id)
        partner = invoices[0].partner_id
        if invoices[0].type in ('out_invoice', 'out_refund'):
            journal = partner.payment_method_customer_id.journal_id
            payment_method_id = partner.payment_method_customer_id
        elif invoices[0].type in ('in_invoice', 'in_refund'):
            journal = partner.payment_method_suppliers_id.journal_id
            payment_method_id = partner.payment_method_suppliers_id

        if not journal:
            raise exceptions.Warning(_('Error'),
                                     _('Please indicate a journal for payment mode %s and company %s') % (payment_method_id.name,
                                                                                                          invoices[0].company_id.name))
        vals = {
            'type': 'payment',
            'journal_id': journal.id,
            'company_id': company_id,
            'partner_id': partner.id,
            'account_id': journal.default_credit_account_id.id or journal.default_debit_account_id.id,
            'amount': self._get_amount(invoices),
            'payment_type': 'G',
            'payment_method_id': payment_method_id.id,
            'partner_bank_necessary': payment_method_id.partner_bank_necessary,
            'partner_bank_id': invoices[0].partner_bank_id.id,
        }

        line_vals = self.env['account.voucher']._get_line_vals_from_invoices(invoices, vals)
        if not line_vals:
            return {}
        vals['line_ids'] = [(0, 0, lv) for lv in line_vals]
        return vals

    @api.model
    def generate_grouped_payments(self):
        logger = self._context.get('logger', _logger)
        voucher_ids = []
        voucher_obj = self.env['account.voucher']
        errors_nb = 0
        for key, invoices in self.get_invoices_to_pay().iteritems():
            vals = self._get_payment_vals(invoices)
            if vals:
                try:
                    voucher_ids.append(voucher_obj.create(vals).id)
                    logger.info(_('Grouped payment created for the following invoices: %s')
                                % (', '.join([inv.number for inv in invoices]),))
                except Exception, e:
                    errors_nb += 1
                    logger.error(_('Grouped payment creation failed for the following invoices: %s - Error: %s')
                                 % (', '.join([inv.number for inv in invoices]), _get_exception_message(e)))
        logger.info(_('%s grouped payments created; %s errors') % (len(voucher_ids), errors_nb))
        return voucher_obj.browse(voucher_ids).execute_end_action()

    @api.multi
    def invoice_pay_by_group(self):
        return self.write({'state': 'progress_paid'})

    @api.multi
    def invoice_pay_customer(self):
        res = super(AccountInvoice, self).invoice_pay_customer()
        invoice = [element for element in self][0]
        payment_method_id = self.env['account.payment.method'].search([], limit=1)
        if not invoice.partner_id.payment_method_customer_id and not payment_method_id:
            raise exceptions.Warning(_('Error'), _('Please indicate a payment mode for customer %s') % (invoice.partner_id.name))
        res['context'].update({
            'default_payment_type': 'I',
            'default_payment_method_id': invoice.partner_id.payment_method_customer_id.id or payment_method_id.id,
            'default_partner_bank_necessary': invoice.partner_id.payment_method_customer_id.partner_bank_necessary,
        })
        return res

    @api.multi
    def set_to_progress_paid(self):
        return self.write({'state': 'progress_paid'})

    @api.multi
    def set_to_open(self):
        return self.write({'state': 'open'})

    @api.multi
    def write(self, values):
        res = super(AccountInvoice, self).write(values)
        partner_ids = []
        for invoice in self:
            partner_id = invoice.partner_id
            if partner_id not in partner_ids:
                partner_ids.append(partner_id)
                has_grouped_payments_in_progress = False
                if partner_id.invoice_ids.search([('state', '=', 'progress_paid'), ('payment_type', '=', 'G')]):
                    has_grouped_payments_in_progress = True
                if partner_id.has_grouped_payments_in_progress != has_grouped_payments_in_progress:
                    partner_id.has_grouped_payments_in_progress = has_grouped_payments_in_progress
        return res
