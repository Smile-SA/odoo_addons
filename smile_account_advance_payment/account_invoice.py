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

from openerp.osv import orm, fields


class AccountInvoice(orm.Model):
    _inherit = 'account.invoice'

    _columns = {
        'purchase_order_ids': fields.many2many('purchase.order', 'purchase_invoice_rel', 'invoice_id', 'purchase_id',
                                               'Purchase Orders', readonly=True),
        'advance_payment_line_ids': fields.one2many('account.voucher.invoice.line', 'invoice_id', 'Advance Payments'),
    }

    def copy_data(self, cr, uid, invoice_id, default=None, context=None):
        default = default or {}
        default['purchase_order_ids'] = []
        default['advance_payment_line_ids'] = []
        return super(AccountInvoice, self).copy_data(cr, uid, invoice_id, default, context=context)

    def action_number(self, cr, uid, ids, context=None):
        res = super(AccountInvoice, self).action_number(cr, uid, ids, context)
        self._recover_advance_payments(cr, uid, ids, context)
        return res

    def _recover_advance_payments(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        advance_payment_line_obj = self.pool.get('account.voucher.invoice.line')
        for invoice, vouchers in self._get_advance_payments(cr, uid, ids, context).iteritems():
            residual = invoice.residual
            for voucher in vouchers:
                if residual and voucher.advance_residual:
                    amount = min(residual, voucher.advance_residual)
                    line_id = advance_payment_line_obj.create(cr, uid, {
                        'invoice_id': invoice.id,
                        'voucher_id': voucher.id,
                        'amount': amount,
                    }, context)
                    advance_payment_line_obj.post(cr, uid, line_id, context)
                    residual -= amount
        return True

    def _get_advance_payments(self, cr, uid, ids, context=None):
        res = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        for invoice in self.browse(cr, uid, ids, context):
            res[invoice] = []
            for purchase_order in invoice.purchase_order_ids:
                for voucher in purchase_order.advance_payment_ids:
                    if voucher.state != 'posted':
                        continue
                    res[invoice].append(voucher)
        return res

    def action_cancel(self, cr, uid, ids, *args):
        advance_payment_line_obj = self.pool.get('account.voucher.invoice.line')
        if isinstance(ids, (int, long)):
            ids = [ids]
        for invoice in self.browse(cr, uid, ids):
            if invoice.advance_payment_line_ids:
                advance_payment_line_obj.unlink(cr, uid, [line.id for line in invoice.advance_payment_line_ids])
        return super(AccountInvoice, self).action_cancel(cr, uid, ids, *args)

    def invoice_pay_customer(self, cr, uid, ids, context=None):
        res = super(AccountInvoice, self).invoice_pay_customer(cr, uid, ids, context)
        res['context']['filter_on_payment_journal'] = True
        return res
