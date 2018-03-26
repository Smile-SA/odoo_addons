# -*- coding: utf-8 -*-
# © 2016 Therp BV <http://therp.nl>
# © 2017 ThinkOpen Solutions <https://tkobr.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from StringIO import StringIO

from PIL import Image, ImageDraw, ImageFont
from PIL import PdfImagePlugin, PalmImagePlugin # noqa # pylint: disable=unused-import
from odoo.tests.common import TransactionCase

from ..models.ir_attachment import _MARKER_PHRASE


class TestDocumentOcr(TransactionCase):
    def test_document_ocr(self):
        self.env['ir.config_parameter'].set_param(
            'document_ocr.synchronous', 'True')
        test_image = Image.new('RGB', (200, 30))
        draw = ImageDraw.Draw(test_image)
        draw.text((3, 3), "Hello world", font=ImageFont.truetype(
            '/usr/share/fonts/truetype/inconsolata/Inconsolata.otf', 24))
        # test a plain image
        data = StringIO()
        test_image.save(data, 'png')
        attachment = self.env['ir.attachment'].create({
            'name': 'testattachment',
            'datas_fname': 'test_png.pdf'})
        result = attachment._index(
            data.getvalue(), 'test.png', None)
        self.assertEqual(result.strip(), 'Hello world')
        # should also work for pdfs
        data = StringIO()
        test_image.save(data, 'pdf', resolution=300)
        attachment = self.env['ir.attachment'].create({
            'name': 'testattachment',
            'datas_fname': 'test_pdf.pdf'})
        result = attachment._index(
            data.getvalue(), 'test.pdf', None)
        self.assertEqual(result.strip(), 'Hello world')
        # check cron
        self.env['ir.config_parameter'].set_param(
            'document_ocr.synchronous', 'False')
        attachment = self.env['ir.attachment'].create({
            'name': 'testattachment',
            'datas_fname': 'test_cron.pdf',
            'datas': data.getvalue().encode('base64'),
        })
        self.assertEqual(attachment.index_content, _MARKER_PHRASE)
        attachment._ocr_cron()
        self.assertEqual(attachment.index_content.strip(), 'Hello world')
        # and for an unreadable image, we expect an empty string
        self.env['ir.config_parameter'].set_param(
            'document_ocr.synchronous', 'True')
        data = StringIO()
        test_image = Image.new('1', (200, 30))
        test_image.save(data, 'palm')
        attachment = self.env['ir.attachment'].create({
            'name': 'testattachment',
            'datas_fname': 'test_err.palm'})
        result = attachment._index(
            data.getvalue(), 'test.palm', None)
        self.assertEqual(result, '')
