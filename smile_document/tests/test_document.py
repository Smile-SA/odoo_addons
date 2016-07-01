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

from mock import patch

import openerp.tests.common as common
from openerp.exceptions import Warning


class test_document(common.TransactionCase):

    def setUp(self):
        super(test_document, self).setUp()
        self.ir_attachment = self.env['ir.attachment']
        self.ir_attachment_type = self.env['ir.attachment.type']

    def test_create_document(self):
        docType1 = self.ir_attachment_type.create({'name': 'Doc Type Test 1'})
        with patch('openerp.fields.Date') as mock_date:
            mock_date.today.return_value = '2016-04-01'
            # Create Valid Doc
            vals1 = {'name': 'Demo1', 'document_type_id': docType1.id, 'expiry_date': '2016-06-01'}
            doc1 = self.ir_attachment.create(vals1)
            self.assertEquals('valid', doc1.status)
            # Archive Doc
            doc1.write({'archived': True})
            self.assertEquals('archived', doc1.status)
        with patch('openerp.fields.Date') as mock_date:
            mock_date.today.return_value = '2016-04-01'
            # Create Expired Doc
            vals2 = {'name': 'Demo2', 'document_type_id': docType1.id, 'expiry_date': '2016-03-12'}
            doc2 = self.ir_attachment.create(vals2)
            self.assertEquals('expired', doc2.status)

    def test_unlink_document_type(self):
        """
            I create a document type.
            I check that I can't unlink document type.
            I check that I can force to unlink document type.
        """
        document_type = self.ir_attachment_type.create({'name': 'Doc Type Test 1'})
        with self.assertRaisesRegexp(Warning, 'Attention : You cannot unlink document type!'):
            document_type.unlink()
        document_type.with_context(force_unlink_doc_type=True).unlink()
