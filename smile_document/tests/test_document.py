# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields
from dateutil.relativedelta import relativedelta

import odoo.tests.common as common
from odoo.exceptions import UserError


class Testdocument(common.TransactionCase):

    def setUp(self):
        super(Testdocument, self).setUp()
        # Force test execution in English, to compare error messages
        self.env.context = dict(self.env.context, lang='en_US')
        self.ir_attachment = self.env['ir.attachment']
        self.ir_attachment_type = self.env['ir.attachment.type']

    def test_create_document(self):
        docType1 = self.ir_attachment_type.create({'name': 'Doc Type Test 1'})
        today = fields.Datetime.now()
        # Create Valid Doc
        d1 = today + relativedelta(months=+2)
        vals1 = {'name': 'Demo1',
                 'document_type_id': docType1.id, 'expiry_date': d1}
        doc1 = self.ir_attachment.create(vals1)
        self.assertEqual('valid', doc1.status)
        # Archive Doc
        doc1.write({'archived': True})
        self.assertEqual('archived', doc1.status)
        # Create Expired Doc
        d2 = today + relativedelta(days=-1)
        vals2 = {'name': 'Demo2',
                 'document_type_id': docType1.id, 'expiry_date': d2}
        doc2 = self.ir_attachment.create(vals2)
        self.assertEqual('expired', doc2.status)

    def test_unlink_document_type(self):
        """
            I create a document type.
            I check that I can't unlink document type.
            I check that I can force to unlink document type.
        """
        document_type = self.ir_attachment_type.create(
            {'name': 'Doc Type Test 1'})
        with self.assertRaisesRegex(
                UserError, 'Attention : You cannot unlink document type!'):
            document_type.unlink()
        document_type.with_context(force_unlink_doc_type=True).unlink()
