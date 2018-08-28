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

import openerp.tests.common as common
from openerp import workflow


class test_account(common.TransactionCase):

    def setUp(self):
        super(test_account, self).setUp()
        self.account_inv = self.env['account.invoice']
        self.sequence = self.env['ir.sequence']
        self.res_partner = self.env['res.partner']
        self.product_id = self.env['product.product']
        self.account_inv_line = self.env['account.invoice.line']
        self.a_period = self.env['account.period']
        company_id = self.env.ref('base.main_company')
        currency_id = self.env.ref('base.EUR')

        # Manage Invoices Dates
        self.today = datetime.now().date()
        self.d1 = self.today
        if self.today.month >= 12:
            self.d1 = self.today.replace(month=self.today.month-1)
        else:
            self.d1 = self.today.replace(month=self.today.month+1)

        # Create Customer
        partner_vals = {'name': 'Customer Test',
                        'is_company': True,
                        'customer': True,
                        'supplier': False}
        partner_id = self.res_partner.create(partner_vals)

        # Create Product
        product_vals = {'name': 'Product Test'}
        product_id = self.product_id.create(product_vals)

        # Create Sequence of type Pcount
        sequence_vals = {'name': 'Sale Sequence Test',
                         'company_id': company_id.id,
                         'implementation': 'pcount',
                         'prefix': 'SALE/%(pyear)s/%(pmonth)s/%(pcount)s'}
        sequence_id = self.sequence.create(sequence_vals)

        # Get journal_id + affect sequence & period_id & account_ids
        self.journal_id = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)[0]
        self.journal_id.sequence_id = sequence_id.id
        a_rec_id = self.env['account.account'].search([('type', '=', 'receivable')], limit=1)[0]
        a_sale_id = self.env['account.account'].search([('type', '=', 'other')], limit=1)[0]

        # INVOICE1
        inv_vals1 = {'partner_id': partner_id.id,
                     'journal_id': self.journal_id.id,
                     'company_id': company_id.id,
                     'currency_id': currency_id.id,
                     'account_id': a_rec_id.id,
                     'date_invoice': self.today}
        self.inv_id1 = self.account_inv.create(inv_vals1)

        inv_line_vals1 = {'product_id': product_id.id,
                          'account_id': a_sale_id.id,
                          'name': '[PC-DEM] PC on Demand 1',
                          'price_unit': 900.0,
                          'quantity': 10.0,
                          'invoice_id': self.inv_id1.id}
        self.inv_line_id1 = self.account_inv_line.create(inv_line_vals1)

        # INVOICE2
        inv_vals2 = {'partner_id': partner_id.id,
                     'journal_id': self.journal_id.id,
                     'company_id': company_id.id,
                     'currency_id': currency_id.id,
                     'account_id': a_rec_id.id,
                     'date_invoice': self.today}
        self.inv_id2 = self.account_inv.create(inv_vals2)

        inv_line_vals2 = {'product_id': product_id.id,
                          'account_id': a_sale_id.id,
                          'name': '[PC-DEM] PC on Demand 2',
                          'price_unit': 800.0,
                          'quantity': 5.0,
                          'invoice_id': self.inv_id2.id}
        self.inv_line_id2 = self.account_inv_line.create(inv_line_vals2)

        # INVOICE3
        inv_vals3 = {'partner_id': partner_id.id,
                     'journal_id': self.journal_id.id,
                     'company_id': company_id.id,
                     'currency_id': currency_id.id,
                     'account_id': a_rec_id.id,
                     'date_invoice': self.d1}
        self.inv_id3 = self.account_inv.create(inv_vals3)

        inv_line_vals3 = {'product_id': product_id.id,
                          'account_id': a_sale_id.id,
                          'name': '[PC-DEM] PC on Demand 3',
                          'price_unit': 400.0,
                          'quantity': 2.0,
                          'invoice_id': self.inv_id3.id}
        self.inv_line_id3 = self.account_inv_line.create(inv_line_vals3)

        # GET PERIODS
        self.period_id1 = self.a_period.find(self.inv_id1.date_invoice)
        self.period_id2 = self.a_period.find(self.inv_id2.date_invoice)
        self.period_id3 = self.a_period.find(self.inv_id3.date_invoice)

    def compute_pcount(self, journal_id, period_id):
        self.cr.execute("""SELECT COUNT(*)
                           FROM account_move
                           WHERE state = %s
                           AND journal_id = %s
                           AND period_id = %s""", ('posted', journal_id, period_id))
        pcount = int(self.cr.fetchall()[0][0]) + 1
        return pcount

    def test_invoices_sequence(self):
        # Open Invoice1
        pcount = self.compute_pcount(self.journal_id.id, self.period_id1.id)
        pmonth = self.today.month
        if len(str(pmonth)) == 1:
            pmonth = '0'+str(pmonth)
        else:
            pmonth = str(pmonth)
        workflow.trg_validate(self.uid, 'account.invoice', self.inv_id1.id, 'invoice_open', self.cr)
        self.assertTrue(self.inv_id1.state == 'open')
        self.assertTrue(self.inv_id1.move_id.name == 'SALE/%s/%s/%05d' % (self.today.year, pmonth, pcount))
        self.assertTrue(self.inv_id1.number == 'SALE/%s/%s/%05d' % (self.today.year, pmonth, pcount))

        # Open Invoice2
        pcount2 = self.compute_pcount(self.journal_id.id, self.period_id2.id)
        pmonth2 = self.today.month
        year2 = self.today.year
        if len(str(pmonth2)) == 1:
            pmonth2 = '0'+str(pmonth2)
        else:
            pmonth2 = str(pmonth2)
        workflow.trg_validate(self.uid, 'account.invoice', self.inv_id2.id, 'invoice_open', self.cr)
        self.assertTrue(self.inv_id2.state == 'open')
        self.assertTrue(self.inv_id2.move_id.name == 'SALE/%s/%s/%05d' % (year2, pmonth2, pcount2))
        self.assertTrue(self.inv_id2.number == 'SALE/%s/%s/%05d' % (year2, pmonth2, pcount2))

        # Open Invoice3
        pcount3 = self.compute_pcount(self.journal_id.id, self.period_id3.id)
        pmonth3 = self.d1.month
        if len(str(pmonth3)) == 1:
            pmonth3 = '0'+str(pmonth3)
        else:
            pmonth3 = str(pmonth3)
        workflow.trg_validate(self.uid, 'account.invoice', self.inv_id3.id, 'invoice_open', self.cr)
        self.assertTrue(self.inv_id2.state == 'open')
        self.assertTrue(self.inv_id3.move_id.name == 'SALE/%s/%s/%05d' % (self.d1.year, pmonth3, pcount3))
        self.assertTrue(self.inv_id3.number == 'SALE/%s/%s/%05d' % (self.d1.year, pmonth3, pcount3))
