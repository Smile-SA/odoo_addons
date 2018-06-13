# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    state = fields.Selection(
        selection_add=[('progress_paid', 'Scheduled Payment')])
    partner_bank_required = fields.Boolean(
        related='partner_id.payment_method_id.partner_bank_required',
        readonly=True, store=True)
    partner_bank_id = fields.Many2one(
        'res.partner.bank', 'Bank Account', readonly=True,
        states={'draft': [('readonly', False)], 'open': [('readonly', False)]})

    @api.onchange('partner_id')
    def _onchange_partner(self):
        if self.partner_bank_required:
            self.partner_bank_id = self.partner_id.bank_ids and \
                self.partner_id.bank_ids[0]

    @api.multi
    def set_to_progress_paid(self):
        return self.filtered(lambda inv: inv.state == 'open'). \
            write({'state': 'progress_paid'})

    @api.multi
    def set_to_open(self):
        return self.filtered(lambda inv: inv.state == 'progress_paid'). \
            write({'state': 'open'})

    @api.model
    @api.returns('account.payment', lambda records: records.ids)
    def generate_payments(self):
        payments = self.env['account.payment']
        for invoices in self._get_invoices_to_pay().values():
            vals = invoices._get_group_payment_vals()
            if vals['amount']:
                payments |= self.env['account.payment'].create(vals)
            else:
                invoices.mapped('move_id.line_ids').auto_reconcile_lines()
        return payments

    @api.model
    def _get_invoices_to_pay(self):
        groups = {}
        domain = [
            ('type', 'in', ('in_invoice', 'in_refund')),
            ('state', '=', 'progress_paid'),
            ('residual', '!=', 0.0),
            '|',
            ('date_due', '=', False),  # Refunds
            ('date_due', '<=', fields.Date.today()),
        ]
        for invoice in self.search(domain):
            key = invoice._get_group_payment_key()
            groups.setdefault(key, self.browse())
            groups[key] |= invoice
        return groups

    @api.multi
    def _get_group_payment_key(self):
        self.ensure_one()
        return self.partner_id.id, \
            self.partner_id.payment_mode == 'I' and \
            self.id or self.partner_id.payment_mode, \
            self.partner_id.payment_method_id.id, \
            self.partner_bank_id.id, \
            self.company_id.id

    @api.multi
    def _get_group_payment_vals(self):
        company = self.mapped('company_id')
        payment_method = self.mapped('partner_id.payment_method_id')
        payment_journal = self.env['account.journal'].search([
            ('outbound_payment_method_ids', 'in', payment_method.ids),
            ('company_id', '=', company.id),
        ], limit=1)
        if not payment_journal:
            raise UserError(
                _('Please create a bank journal for the payment method '
                  '%s and the company %s')
                % (payment_method.name, company.name))
        return {
            'invoice_ids': [(6, 0, self.ids)],
            'amount': max(sum(self.mapped('residual_signed')), 0),
            'payment_date': fields.Date.context_today(self),
            'communication':
                ', '.join(x for x in self.mapped('reference') if x),
            'partner_id': self.mapped('partner_id').id,
            'partner_type': 'supplier',
            'journal_id': payment_journal.id,
            'payment_type': payment_method.payment_type,
            'payment_method_id': payment_method.id,
        }
