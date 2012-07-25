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
from datetime import datetime, timedelta
from smile_invoicing_plan.invoicing_plan_tools import compute_date



class account_invoicer(osv.osv):
    _name = 'account.invoicer'

    _columns = {
            'periodic_sale_order_ids': fields.many2many('sale.order', 'sale_order_invoicer_rel', 'invoicer_id', 'sale_order_id', 'Sale orders'),
            'non_periodic_sale_order_ids': fields.many2many('sale.order', 'np_sale_order_invoicer_rel', 'invoicer_id', 'sale_order_id', 'Sale orders'),
            'invoice_ids': fields.many2many('account.invoice', 'invoices_invoicer_rel', 'invoice_id', 'invoicer_id', 'Sale orders'),
            'name': fields.char('Name', size=64, required=True),
            'start_date': fields.date('Start period date'),
            'end_date': fields.date('End period date'),
            'invoice_outof_period': fields.boolean('Invoice out of period', required=False, help='Retrieve all subscription that invoicing next date is lower than end_date'),
            'invoice_contracts': fields.boolean('Invoice contracts', required=False, help='Include invoicing contracts'),
            'invoice_non_contracts': fields.boolean('Invoice sale orders', required=False, help='Include invoicing sale orders'),
                    }
    _defaults = {
        'name': lambda *a: time.strftime('%Y-%m-%d'),
        'invoice_contracts': lambda *a: True,
        'invoice_outof_period': lambda *a: True,
        'start_date': lambda *a: time.strftime('%Y-%m-%d'),
        }


    def get_sale_orders2invoice(self, cr, uid, ids, context={}):
        sale_order_ids = []

        invoicer = self.browse(cr, uid, ids)[0]

        perdiodic_sale_order2invoice_ids = self.pool.get('sale.order').search(cr, uid, [('invoicing_next_date', '<=', invoicer.end_date),
                                                                                      ('contract_ok', '=', True),
                                                                    #('invoicing_next_date', '>=', invoicer.start_date),
                                                                    '|', ('state', '=', 'progress'), ('state', '=', 'manual'),
                                                                    ])



        non_perdiodic_sale_order2invoice_ids = self.pool.get('sale.order').search(cr, uid, [('contract_ok', '=', False),
                                                                                          '|',
                                                                                          ('state', '=', 'progress'), ('state', '=', 'manual'),
                                                                    ])


        self.write(cr, uid, ids, {'periodic_sale_order_ids': [(6, 0, perdiodic_sale_order2invoice_ids)],
                        'non_periodic_sale_order_ids': [(6, 0, non_perdiodic_sale_order2invoice_ids)]})
        return True

    def pre_invoice(self, cr, uid, ids, context={}):
        ## create invoices in draft state
        invoicer = self.browse(cr, uid, ids)[0]
        if not context:
            context={}

        contract2invoice_ids = []
        sale_order_ids = []

        context.update({'invoicing_period': {'start_date':  invoicer.start_date,
                                            'end_date':  invoicer.end_date,
                                            },
                        'invoice_contracts': invoicer.invoice_contracts,
                        'invoice_non_contracts': invoicer.invoice_non_contracts,
                        'invoice_outof_period': invoicer.invoice_outof_period,
                                 })

        if invoicer.invoice_contracts:
            cr.execute('select sale_order_id from sale_order_invoicer_rel where invoicer_id=%s', (invoicer.id, ))
            res = cr.fetchall()

            if res:
                contract2invoice_ids = [x[0] for x in res]

        if invoicer.invoice_non_contracts:

            cr.execute('select sale_order_id from np_sale_order_invoicer_rel where invoicer_id=%s', (invoicer.id, ))
            res = cr.fetchall()

            if res:
                sale_order_ids = [x[0] for x in res]

        sale_order_ds = contract2invoice_ids + sale_order_ids

        invoice_ids = self.pool.get('sale.order').action_invoice_create(cr, uid, sale_order_ds, False, ['confirmed', 'done', 'exception'], False, context)

        if invoice_ids:
            invoicer.write({'invoice_ids': [(6, 0, invoice_ids)]})
        return True


account_invoicer()


