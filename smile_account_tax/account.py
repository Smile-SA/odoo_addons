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

from openerp import netsvc
from openerp.osv import orm, fields
from openerp.tools.translate import _


class AccountTax(orm.Model):
    _inherit = 'account.tax'

    _columns = {
        'date_start': fields.date('Start date'),
        'date_stop': fields.date('End date'),
    }


class AccountInvoice(orm.Model):
    _inherit = 'account.invoice'

    _columns = {
        'date_invoice_supplier': fields.date('Supplier date', readonly=True, states={'draft': [('readonly', False)]}),
    }

    def _open_tax_wizard(self, cr, uid, ids, message, context=None):
        context = context and context.copy() or {}
        context['default_invoice_ids'] = ids
        context['default_message'] = message
        return {
            'name': _('Unvalid taxes'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice.tax.wizard',
            'target': 'new',
            'context': context,
            'nodestroy': False,
        }

    def invoice_open(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        error_msg = []
        for invoice in self.browse(cr, uid, ids, context):
            date = invoice.type in ('in_invoice', 'in_refund') and invoice.date_invoice_supplier or invoice.date_invoice or time.strftime('%Y-%m-%d')
            for line in invoice.invoice_line:
                for tax in line.invoice_line_tax_id:
                    if (tax.date_start and tax.date_start > date) or (tax.date_stop and tax.date_stop < date):
                        error_msg.append(_("The tax '%' in the invoice line '%s' is not valid to %s") % (tax.name, line.name, date))
        if error_msg:
            return self._open_tax_wizard(cr, uid, ids, '\n'.join(error_msg), context)
        wf_service = netsvc.LocalService('workflow')
        for invoice_id in ids:
            wf_service.trg_validate(uid, 'account.invoice', invoice_id, 'invoice_open', cr)
        return True
