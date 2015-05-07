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


class test_document(common.TransactionCase):

    def setUp(self):
        super(test_document, self).setUp()
        self.ir_attachment = self.env['ir.attachment']

    def test_create_document(self):
        doc_type_kbis = self.env.ref('adc_document.doc_type_kbis')
        today = datetime.now().date()
        # Create Valid Doc
        print "==================> Create Document Successfully!"
        d1 = today.replace(month=today.month+2)
        vals1 = {'name': 'Demo1', 'document_type_id': doc_type_kbis.id, 'expiry_date': d1}
        doc1 = self.ir_attachment.create(vals1)
        self.assertTrue(doc1.status == 'valid')
        # Archive Doc
        doc1.write({'archived': True})
        self.assertTrue(doc1.status == 'archived')
        print "==================> Archive Document Successfully!"
        # Create Expired Doc
        d2 = today.replace(day=today.day-1)
        vals2 = {'name': 'Demo2', 'document_type_id': doc_type_kbis.id, 'expiry_date': d2}
        doc2 = self.ir_attachment.create(vals2)
        self.assertTrue(doc2.status == 'expired')
        print "==================> Expire Document Successfully!"
