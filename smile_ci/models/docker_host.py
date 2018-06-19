# -*- coding: utf-8 -*-

import logging
from urlparse import urljoin, urlparse

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import config

_logger = logging.getLogger(__name__)


class DockerHost(models.Model):
    _inherit = 'docker.host'

    @api.model
    def _get_default_build_base_url(self):
        if config.get('build_base_url'):
            base_url = config.get('build_base_url')
        else:
            base_url = self.env['ir.config_parameter'].get_param(
                'web.base.url')
        netloc = urlparse(base_url).netloc
        port = netloc.split(':')[-1]
        netloc = netloc.replace(':%s' % port, '')
        return urljoin(base_url, '//%s' % netloc)

    @api.model
    def _get_default_redirect_subdomain_to_port(self):
        return config.get('redirect_subdomain_to_port') or False

    build_base_url = fields.Char(
        required=True, default=_get_default_build_base_url)
    redirect_subdomain_to_port = fields.Boolean(
        default=_get_default_redirect_subdomain_to_port)
    builds_host_config = fields.Text()
    port_range = fields.Char(default='8100,8200,2')

    @api.multi
    def get_build_url(self, port):
        self.ensure_one()
        netloc = urlparse(self.build_base_url).netloc
        netloc_wo_auth = netloc.split('@')[-1]
        if self.redirect_subdomain_to_port:
            # Add subdomain
            auth = ''
            if '@' in netloc:
                auth, netloc = netloc.split('@')
                auth += '@'
            if netloc.startswith('www.'):
                netloc.replace('www.', '')
            return urljoin(
                self.build_base_url, '//%sbuild_%s.%s' % (auth, port, netloc))
        # Replace default port
        if ':' in netloc_wo_auth:
            default_port = netloc_wo_auth.split(':')[-1]
            netloc = netloc_wo_auth.replace(':%s' % default_port, '')
        return urljoin(self.build_base_url, '//%s:%s' % (netloc, port))

    @api.multi
    def find_ports(self):
        self.ensure_one()
        _logger.info('Searching available ports...')
        range_args = map(int, self.port_range.split(','))
        available_ports = set(range(*range_args))
        Build = self.env['scm.repository.branch.build']
        build_infos = Build.search_read([
            ('docker_host_id', '=', self.id),
            ('port', '!=', False),
        ], ['port'])
        busy_ports = {int(b['port']) for b in build_infos if b['port']}
        available_ports -= busy_ports
        if not available_ports:
            raise UserError(_('No available ports'))
        return sorted(available_ports, reverse=True)
