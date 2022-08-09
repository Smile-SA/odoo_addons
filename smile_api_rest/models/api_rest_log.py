# -*- coding: utf-8 -*-
# (C) 2022 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import fields, models, api
from odoo.http import request


RESPONSE_DATA_MAX_CHARACTERS = 5000


class ApiRestLog(models.Model):
    _name = 'api.rest.log'
    _order = 'create_date desc'
    _description = "Api Rest Log"

    version_id = fields.Many2one(
        'api.rest.version', required=True, ondelete='cascade')
    request_url = fields.Char()
    request_headers = fields.Char()
    request_data = fields.Char()
    response_data = fields.Char()
    length_response_data = fields.Integer(
        compute='_get_infos_response_data', store=True)
    summary_response_data = fields.Text(
        'Details', compute='_get_infos_response_data', store=True)
    file_response_data = fields.Binary(
        compute='_get_infos_response_data', store=True)
    filename_response_data = fields.Char(
        compute='_get_infos_response_data', store=True)

    @api.depends('response_data')
    def _get_infos_response_data(self):
        for record in self:
            response_data = record.response_data
            length_response_data = len(response_data)
            summary_response_data = response_data
            if length_response_data > RESPONSE_DATA_MAX_CHARACTERS:
                summary_response_data = \
                    response_data[:RESPONSE_DATA_MAX_CHARACTERS]
                summary_response_data += '.....'
            record.length_response_data = length_response_data
            record.summary_response_data = summary_response_data
            record.file_response_data = \
                base64.b64encode(response_data.encode())
            record.filename_response_data = \
                'response_data_{}.log'.format(record.id)

    def create_log(self, version_id, request_data, response_data, user=False):
        public_user = self.env.ref('base.public_user')
        log = self.sudo().with_user(user or public_user).create({
            'version_id': version_id,
            'request_url': request.httprequest.base_url,
            'request_headers': request.httprequest.headers,
            'request_data': request_data,
            'response_data': response_data,
        })
        log.sudo().version_id.last_usage_date = fields.Datetime.now()
        return log
