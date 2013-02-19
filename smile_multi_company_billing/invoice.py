# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-2012 Smile (<http://www.smile.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields
import tools
from tools.translate import _


def _get_exception_message(exception):
    msg = isinstance(exception, osv.except_osv) and exception.value or exception
    return tools.ustr(msg)


class Invoice(osv.osv):
    _inherit = 'account.invoice'

    _columns = {
        'original_invoice_id': fields.many2one('account.invoice', "Original Invoice", readonly=True),
    }

    def _get_journal_id(self, cr, uid, company_id, invoice_type, context=None):
        journal_id = False
        journal_types_from_invoice_types = {
            'out_invoice': 'sale',
            'in_invoice': 'purchase',
            'out_refund': 'sale_refund',
            'in_refund': 'purchase_refund',
        }
        journal_type = journal_types_from_invoice_types[invoice_type]
        journal_ids = self.pool.get('account.journal').search(cr, uid, [('company_id', '=', company_id), ('type', '=', journal_type)])
        if journal_ids:
            journal_id = journal_ids[0]
        default_journals = self.pool.get('ir.values').get(cr, uid, 'default', 'type=%s' % (invoice_type), ['account.invoice'])
        for journal in default_journals:
            if journal[1] == 'journal_id' and journal[2] in journal_ids:
                journal_id = journal[2]
        if not journal_id:
            company_name = self.pool.get('res.company').read(cr, uid, company_id, ['name'], context)['name']
            raise osv.except_osv(_('Configuration Error !'), (_('Can\'t find any account journal of %s type '
                                                                'for the company %s.\n\nYou can create one in the menu: \n'
                                                                'Configuration\Financial Accounting\Accounts\Journals.')
                                                              % (journal_type, company_name)))
        context = context or {}
        return self.get_journal_from_fiscal_position(cr, uid, context.get('invoice_fiscal_position'), journal_id)

    def _get_invoice_lines(self, cr, uid, invoice, context=None):
        invoice_lines = []
        for line in invoice.invoice_line:
            name = line.name
            product_id = line.product_id.id
            uos_id = line.uos_id.id
            quantity = line.quantity
            price_unit = line.price_unit
            invoice_line_vals = self.pool.get('account.invoice.line').product_id_change(cr, uid, False, product_id, uos_id,
                                                                                        line.quantity, name, context.get('invoice_type', False),
                                                                                        context.get('invoice_partner_id', False),
                                                                                        context.get('invoice_fiscal_position', False), price_unit,
                                                                                        context.get('partner_address_invoice_id', False),
                                                                                        context.get('invoice_currency_id', False), context
                                                                                        )['value']
            invoice_line_vals.update({
                'name': name,
                'origin': line.origin,
                'uos_id': uos_id,
                'product_id': product_id,
                'price_unit': line.price_unit,
                'quantity': quantity,
                'discount': line.discount,
                'note': line.note,
            })
            invoice_lines.append(invoice_line_vals)
        return invoice_lines

    def create_inter_company_invoices(self, cr, uid, ids, context=None):
        context_copy = dict(context or {})
        if isinstance(ids, (int, long)):
            ids = [ids]
        for invoice in self.browse(cr, uid, ids, context):
            if not invoice.original_invoice_id and invoice.partner_id.partner_company_id:
                invoice_type = invoice.type.startswith('in_') and invoice.type.replace('in_', 'out_') or invoice.type.replace('out_', 'in_')
                partner_id = invoice.company_id.partner_id.id
                date_invoice = invoice.date_invoice
                payment_term = invoice.payment_term.id
                partner_bank_id = invoice.partner_bank_id.id
                company_id = invoice.partner_id.partner_company_id.id
                currency_id = invoice.currency_id.id
                invoice_vals = self.onchange_partner_id(cr, uid, False, invoice_type, partner_id, date_invoice,
                                                        payment_term, partner_bank_id, company_id)['value']
                context_copy.update({
                    'company_id': company_id,
                    'invoice_type': invoice_type,
                    'invoice_partner_id': partner_id,
                    'invoice_fiscal_position': invoice_vals.get('fiscal_position', False),
                    'invoice_currency_id': currency_id,
                    'partner_address_invoice_id': invoice_vals.get('address_invoice_id', False),
                })
                invoice_vals.update({
                    'origin': invoice.origin,
                    'original_invoice_id': invoice.id,
                    'type': invoice_type,
                    'reference': invoice.number,
                    'date_invoice': date_invoice,
                    'date_due': invoice.date_due,
                    'partner_id': partner_id,
                    'currency_id': currency_id,
                    'journal_id': self._get_journal_id(cr, uid, company_id, invoice_type, context_copy),
                    'company_id': company_id,
                    'user_id': False,
                    'invoice_line': map(lambda x: (0, 0, x), self._get_invoice_lines(cr, uid, invoice, context_copy)),
                    'check_total': invoice.amount_total,
                })
                self.create(cr, 1, invoice_vals, context)  # To bypass access and record rules
        return True

    def action_number(self, cr, uid, ids, context=None):
        """Override this original method to create invoice for the supplier/customer company"""
        res = super(Invoice, self).action_number(cr, uid, ids, context)
        self.create_inter_company_invoices(cr, uid, ids, context)
        return res

    def get_fiscal_position_domain(self, cr, uid, company_id, company_dest_id, context=None):
        if company_id and company_dest_id:
            return [('company_id', '=', company_id), ('company_dest_id', '=', company_dest_id), ('type', '=', 'inter')]
        return []

    def get_fiscal_position_id(self, cr, uid, company_id, company_dest_id, context=None):
        if not company_id or not company_dest_id:
            return
        domain = self.get_fiscal_position_domain(cr, uid, company_id, company_dest_id, context)
        fiscal_position_ids = self.pool.get('account.fiscal.position').search(cr, uid, domain, limit=1)
        if not fiscal_position_ids:
            company_obj = self.pool.get('res.company')
            company_name = company_obj.read(cr, uid, company_id, ['name'])['name']
            company_dest_name = company_obj.read(cr, uid, company_dest_id, ['name'])['name']
            raise osv.except_osv(_('Error'), _('Inter-billing fiscal position for the company %s to the company %s not found. Please create one')
                                 % (company_name, company_dest_name))
        return fiscal_position_ids[0]

    def _update_onchange_result_with_fiscal_position(self, cr, uid, res, company_id, partner_id):
        res = res or {}
        if company_id and partner_id:
            partner_company_id = self.pool.get('res.partner').read(cr, uid, partner_id, ['partner_company_id'],
                                                                   load='_classic_write')['partner_company_id']
            if partner_company_id:
                fiscal_position_id = self.get_fiscal_position_id(cr, uid, company_id, partner_company_id)
                res.setdefault('value', {}).update({'fiscal_position': fiscal_position_id})
                res.setdefault('domain', {}).update({'fiscal_position': fiscal_position_id})
        return res

    def onchange_partner_id(self, cr, uid, ids, type_, partner_id, date_invoice=False,
                            payment_term=False, partner_bank_id=False, company_id=False):
        res = super(Invoice, self).onchange_partner_id(cr, uid, ids, type_, partner_id, date_invoice,
                                                       payment_term, partner_bank_id, company_id)
        self._update_onchange_result_with_fiscal_position(cr, uid, res, company_id, partner_id)
        return res

    def onchange_company_id(self, cr, uid, ids, company_id, partner_id, type_, invoice_line, currency_id):
        try:
            res = super(Invoice, self).onchange_company_id(cr, uid, ids, company_id, partner_id, type_, invoice_line, currency_id)
            self._update_onchange_result_with_fiscal_position(cr, uid, res, company_id, partner_id)
            return res
        except Exception, e:
            return {'warning': {'title': _('Warning'), 'message': _get_exception_message(e)}}
Invoice()
