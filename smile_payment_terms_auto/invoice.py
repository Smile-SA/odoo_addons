# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Smile (<http://www.smile.fr>). All Rights Reserved
#                       author cyril.gaspard@smile.fr
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
from openerp.osv import fields, orm
from openerp import SUPERUSER_ID
from openerp.tools import ustr
import time


class Invoice(orm.Model):
    _inherit = 'account.invoice'

    def onchange_payment_terms_id(self, cr, uid, ids, payment_terms_id):
        context = {}
        pay_auto = False
        if payment_terms_id:
            payment_term = self.pool.get('payment.terms.partner').browse(cr, SUPERUSER_ID, payment_terms_id, context=context)
            pay_auto = payment_term.pay_auto or False
            if not pay_auto:
                return {'value': {'pay_auto': pay_auto, 'reference': ''}}
            return {'value': {'pay_auto': pay_auto}}
        return {'value': {'pay_auto': pay_auto, 'reference': ''}}

    _columns = {
        'reference': fields.char('Ref #', size=64, help="Transaction reference number."),
        'pay_auto': fields.related('payment_terms_id', 'pay_auto', string="Pay Auto", type='boolean')
    }

    def invoice_validate(self, cr, uid, ids, context=None):
        context = context or {}
        voucher_obj = self.pool.get('account.voucher')
        res = super(Invoice, self).invoice_validate(cr, uid, ids, context)
        for invoice in self.browse(cr, SUPERUSER_ID, ids, context):
            if invoice.payment_terms_id and invoice.payment_terms_id.pay_auto:
                ttype = invoice.type in ('out_invoice', 'out_refund') and 'receipt' or 'payment' or False
                if ttype:
                    context.update({'payment_expected_currency': invoice.currency_id.id,
                                    'close_after_process': True,
                                    'invoice_type': invoice.type,
                                    'invoice_id': invoice.id,
                                    'type': ttype,
                                    })
                    currency_id = invoice.currency_id.id
                    journal_id = invoice.payment_terms_id.property_account_journal.id
                    partner_id = invoice.partner_id.id
                    amount = invoice.type in ('out_refund', 'in_refund') and -invoice.residual or invoice.residual
                    date = time.strftime('%Y-%m-%d')
                    partner_child_id = self.pool.get('res.partner').browse(cr, uid, partner_id, context)
                    if partner_child_id.parent_id:
                        partner_id = partner_child_id.parent_id.id
                    data = voucher_obj.onchange_partner_id(cr, uid, [], partner_id,
                                                           journal_id,
                                                           amount,
                                                           currency_id,
                                                           ttype,
                                                           date,
                                                           context)
                    name = invoice.number
                    dico = data.get('value', {})
                    dico.update({'reference': invoice.reference,
                                 'journal_id': journal_id,
                                 'amount': amount,
                                 'name': name,
                                 'partner_id': partner_id})
                    dico['line_cr_ids'] = [(0, 0, x) for x in dico['line_cr_ids'] if x.get('name') and
                                           invoice.number and x.get('name') == ustr(invoice.number)]
                    dico['line_dr_ids'] = [(0, 0, x) for x in dico['line_dr_ids'] if x.get('name') and
                                           invoice.number and x.get('name') == ustr(invoice.number)]
                    ## SUPERUSER_ID
                    voucher_id = voucher_obj.create(cr, SUPERUSER_ID, dico, context)
                    voucher_obj.button_proforma_voucher(cr, SUPERUSER_ID, [voucher_id], context=context)
        return res
