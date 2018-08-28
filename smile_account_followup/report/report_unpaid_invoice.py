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

from datetime import datetime
from openerp.osv import osv
from openerp.report import report_sxw


class UnpaidInvoiceReport(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(UnpaidInvoiceReport, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            '_get_invoice_data': self._get_invoice_data,
            '_get_invoice_action': self._get_invoice_action,
        })

    def _get_invoice_data(self, invoice_id):
        invoice = self.pool['account.invoice'].browse(self.cr, self.uid, invoice_id)
        paid_amount = sum([payment.credit for payment in invoice.payment_ids])
        return {
            'invoice_date': invoice.date_invoice,
            'number': invoice.number,
            'due_date': invoice.date_due,
            'invoice_amount': invoice.amount_total,
            'paid_amount': paid_amount,
            'unpaid_amount': invoice.amount_total - paid_amount,
            'action_reminder_ids': [action.id for action in invoice.action_reminder_ids],
        }

    def _get_invoice_action(self, action_id):
        action = self.pool['action.reminder'].browse(self.cr, self.uid, action_id)
        action_date = datetime.strptime(action.date, '%Y-%m-%d').strftime('%d/%m/%Y')
        return {
            'action_done': 1 if action.action_done else 0,
            'action': action_date + '   ' + action.level_reminder_id.code + '   ' + action.name,
        }


class UnpaidInvoiceReports(osv.AbstractModel):
    _name = 'report.smile_account_followup.report_unpaid_invoice'
    _inherit = 'report.abstract_report'
    _template = 'smile_account_followup.report_unpaid_invoice'
    _wrapped_report_class = UnpaidInvoiceReport
