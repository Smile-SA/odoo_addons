# -*- coding: utf-8 -*-
# (C) 2022 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from werkzeug import urls

from odoo import api, fields, models, _
from odoo.http import request


class ApiRestVersion(models.Model):
    _name = 'api.rest.version'

    name = fields.Char(string='Number Version', required=True)
    active = fields.Boolean(default=True)
    description = fields.Html()
    url_api_docs = fields.Char(compute='_compute_urls')
    url_swagger = fields.Char(compute='_compute_urls')
    path_ids = fields.One2many(
        'api.rest.path', 'version_id', string='Paths',
        context={'active_test': False})
    # Security
    user_ids = fields.Many2many('res.users', string='Users')
    # Logs
    active_log = fields.Boolean()
    last_usage_date = fields.Datetime()
    log_ids = fields.One2many(
        'api.rest.log', 'version_id', string='Logs', readonly=True)

    def _compute_urls(self):
        base_url = request.httprequest.host_url
        for record in self:
            record.url_api_docs = urls.url_join(
                base_url, '/api-docs/v{}'.format(record.name))
            record.url_swagger = urls.url_join(
                base_url, '/api-docs/v{}/swagger.json'.format(record.name))

    @api.model
    def create(self, values):
        version = super().create(values)
        user = self.env.ref('base.user_admin')
        if user and user not in self.user_ids:
            version.user_ids = [(4, user.id)]
            user.generate_api_rest_key()
        return version

    def go_to_api_docs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.url_api_docs,
            'target': '_new',
        }

    def get_swagger_json(self):
        self.ensure_one()
        web_base_url = \
            self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        parsed_url = urls.url_parse(web_base_url)
        paths = self.sudo().path_ids.filtered(lambda p: p.active)
        # Tags
        swagger_tags = []
        for tag in paths.mapped('tag_id'):
            swagger_tags.append({
                'name': tag.name or '',
                'description': tag.description or '',
            })
        swagger_paths, swagger_definitions = {}, {}
        for path in paths:
            # Paths
            path._generate_path(swagger_paths)
            # Definitions
            path._generate_definition(swagger_definitions)
        return {
            'swagger': '2.0',
            'info': {
                'version': '{}'.format(self.name),
                'title': 'API Rest'.format(self.name),
                'description': self.get_swagger_description(),
            },
            'host': parsed_url.netloc,
            'schemes': [parsed_url.scheme],
            'basePath': '/api/v{}'.format(self.name),
            'paths': swagger_paths,
            'tags': swagger_tags,
            'securityDefinitions': {
                'api_key': {
                    'type': 'apiKey',
                    'name': 'x-api-key',
                    'in': 'header',
                },
            },
            'definitions': swagger_definitions,
        }

    def get_swagger_description(self):
        self.ensure_one()
        description = self.description or ''
        others_api = self.search(
            [('id', '!=', self.id)]
        )
        if others_api:
            description += '\n\n {}'.format(
                _('<b>Others API available: </b>'))
            for url_api in others_api:
                description += '\n- [{url}]({url})'.format(
                    url=url_api.url_api_docs)
        return description
