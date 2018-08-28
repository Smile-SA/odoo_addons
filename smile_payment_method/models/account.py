# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) OpenERP Venezuela (<http://openerp.com.ve>).
#    All Rights Reserved
# Credits######################################################
#    Coded by: Vauxoo C.A.
#    Planified by: Nhomar Hernandez
#    Audited by: Vauxoo C.A.
#############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##########################################################################
from openerp import models, fields, api, exceptions
from openerp.tools.translate import _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    payment_method_id = fields.Many2one('account.payment.method',
                                       string='Payment Method')

    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False,
            payment_term=False, partner_bank_id=False, company_id=False):
        res = super(AccountInvoice, self).onchange_partner_id(type, partner_id, date_invoice, payment_term, partner_bank_id, company_id)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            payment_method_id = False
            if self._context['type'] in ('out_invoice', 'out_refund'):
                payment_method_id = partner.payment_method_customer_id.id
            elif self._context['type'] in ('in_invoice', 'in_refund'):
                payment_method_id = partner.payment_method_suppliers_id.id
            res.get('value', {}).update({'payment_method_id': payment_method_id})
        return res

    def invoice_pay_customer(self, cr, uid, ids, context=None):
        context = context or {}
        if not ids:
            return []
        inv = self.browse(cr, uid, ids[0], context=context)
        res = super(AccountInvoice, self).invoice_pay_customer(cr, uid, ids, context=context)
        res['context']['default_journal_id'] = inv and inv.payment_method_id and \
            inv.payment_method_id.journal_id and inv.payment_method_id.journal_id.id or False
        return res


class AccountInvoiceRefund(models.Model):
    _inherit = "account.invoice.refund"

    @api.multi
    def compute_refund(self, mode='refund'):
        result = super(AccountInvoiceRefund, self).compute_refund(mode=mode)
        if mode == 'refund' and 'domain' in result and 'active_id' in self._context:
            refund_ids = [elt[2][0] for elt in result['domain'] if elt[0] == 'id']
            if len(refund_ids) == 1:
                try:
                    invoice_obj = self.env['account.invoice']
                    invoice = invoice_obj.search([('id', '=', self._context['active_id'])])
                    refund = invoice_obj.search([('id', '=', refund_ids[0])])
                    refund.write({'payment_method_id': invoice.payment_method_id.id or False})
                except:
                    pass
        return result


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    @api.multi    
    def onchange_partner_id(self, partner_id, journal_id, amount, currency_id, ttype, date):
        res = super(AccountVoucher, self).onchange_partner_id(partner_id, journal_id, amount, currency_id, ttype, date)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            payment_journal_id = False
            if self._context['type'] == 'receipt' and not journal_id:
                payment_journal_id = partner.payment_method_customer_id.journal_id.id
            elif self._context['type'] == 'payment' and not journal_id:
                payment_journal_id = partner.payment_method_suppliers_id.journal_id.id
            if payment_journal_id:
                if res.get('value'):
                    res.get('value', {}).update({'journal_id': payment_journal_id})
                else:
                    res['value']={'journal_id': payment_journal_id}
        return res
