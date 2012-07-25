# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Smile (<http: //www.smile.fr>). All Rights Reserved
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
#    along with this program.  If not, see <http: //www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, osv
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

import netsvc
import pooler
from tools.translate import _
import decimal_precision as dp
from osv.orm import browse_record, browse_null


class wizard_compute_commission(osv.osv_memory):

    _name = 'wizard.compute.commission'
    _description = 'Compute Go between commissions'

    _columns = {
            'name': fields.char('Name', size=64, required=True, readonly=True),
            'opened_invoice_ids': fields.many2many('account.invoice', 'invoice_commission_rel', 'invoice_id', 'commission_wizard_id', 'Opened Invoices To Charge'),
            'subscriber_purchase_order_ids': fields.many2many('purchase.order', 'purchase_order_commission_rel', 'commission_wizard_id', 'purchase_order_id', 'Subscriber purchase'),
                    }

    _defaults = {
        'name': 'my name',
        }

    def button_compute(self, cr, uid, ids, context=None):

        cr.execute("select account_invoice.id from account_invoice\
                        inner join account_invoice_line\
                            on     (account_invoice_line.invoice_id = account_invoice.id)\
                                    and (account_invoice.state = 'open')\
                                    and (account_invoice_line.invoice_line2charge_ok = True)\
                                    and (account_invoice_line.charged_ok = False)\
                    group by account_invoice.id ")

        ret = cr.fetchall()

        if ret:
            invoice_ids = [x[0] for x in ret]
            self.write(cr, uid, ids, {'opened_invoice_ids': [(6, 0, invoice_ids)]})

        return True

    def button_generate(self, cr, uid, ids, context=None):
        self.button_compute(cr, uid, ids)
        ret = self.read(cr, uid, ids, ['opened_invoice_ids'])

        if not ret:
            return True

        invoice_ids = []
        for x in ret:
            invoice_ids += x['opened_invoice_ids']

        purchase_ids = self.pool.get('account.invoice').create_subcriber_purchase_order(cr, uid, invoice_ids)

        if purchase_ids:
            self.write(cr, uid, ids, {'subscriber_purchase_order_ids': [(6, 0, purchase_ids)]})
        return True


wizard_compute_commission()