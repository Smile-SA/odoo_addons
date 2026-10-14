# -*- coding: utf-8 -*-
# (C) 2025 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import http, _
from odoo.http import request
from werkzeug.utils import redirect


class WebsiteAttachmentPage(http.Controller):

    def get_attachments(self):
        attachment_ids = request.env['ir.attachment'].sudo().search(
            [('website_published', '=', True)])
        documents = {}
        for record in attachment_ids:
            document_type = record.document_type_id and record.document_type_id.name or _('Others')  # noqa E501
            if document_type in documents:
                documents[document_type].append(record)
            else:
                vals = {document_type: [record]}
                documents.update(vals)
        return documents

    @http.route('/Attachments', type='http', auth="public", website=True)
    def attachment_details(self, **kw):
        return request.render('smile_publish_document.attachment_template',
                              {'attachments': self.get_attachments()})

    @http.route(['/attachment/download'], type='http', auth='public')
    def download_attachment(self, attachment_id, **kw):
        attachment = request.env['ir.attachment'].sudo().search(
            [('id', '=', int(attachment_id)),
             ('website_published', '=', True)])
        if not attachment:
            return redirect('/Attachments')
        if attachment.type == "url":
            if attachment.url:
                return redirect(attachment.url)
            return request.not_found()
        return request.env['ir.binary']._get_stream_from(
            attachment, 'raw', filename_field='name').get_response(
            as_attachment=True)
