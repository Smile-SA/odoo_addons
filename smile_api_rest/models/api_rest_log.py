# -*- coding: utf-8 -*-
# (C) 2021 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models
from odoo.http import request


class ApiRestLog(models.Model):
    _name = 'api.rest.log'
    _order = 'create_date desc'

    version_id = fields.Many2one(
        'api.rest.version', required=True, ondelete='cascade')
    request_url = fields.Char()
    request_headers = fields.Char()
    request_data = fields.Char()
    response_data = fields.Char()

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
