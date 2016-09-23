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

from datetime import date
from dateutil.relativedelta import relativedelta

import openerp.tests.common as common
from openerp.exceptions import UserError


class test_document(common.TransactionCase):

    def setUp(self):
        super(test_document, self).setUp()
        # Force test execution in English, to compare error messages
        self.env.context = dict(self.env.context, lang='en_US')
        self.ir_attachment = self.env['ir.attachment']
        self.ir_attachment_type = self.env['ir.attachment.type']

    def test_create_document(self):
        docType1 = self.ir_attachment_type.create({'name': 'Doc Type Test 1'})
        today = date.today()
        # Create Valid Doc
        d1 = today + relativedelta(months=+2)
        vals1 = {'name': 'Demo1', 'document_type_id': docType1.id, 'expiry_date': d1}
        doc1 = self.ir_attachment.create(vals1)
        self.assertEquals('valid', doc1.status)
        # Archive Doc
        doc1.write({'archived': True})
        self.assertEquals('archived', doc1.status)
        # Create Expired Doc
        d2 = today + relativedelta(days=-1)
        vals2 = {'name': 'Demo2', 'document_type_id': docType1.id, 'expiry_date': d2}
        doc2 = self.ir_attachment.create(vals2)
        self.assertEquals('expired', doc2.status)

    def test_unlink_document_type(self):
        """
            I create a document type.
            I check that I can't unlink document type.
            I check that I can force to unlink document type.
        """
        document_type = self.ir_attachment_type.create({'name': 'Doc Type Test 1'})
        with self.assertRaisesRegexp(UserError, 'Attention : You cannot unlink document type!'):
            document_type.unlink()
        document_type.with_context(force_unlink_doc_type=True).unlink()
