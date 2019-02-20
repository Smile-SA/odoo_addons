# -*- coding: utf-8 -*-

import base64
import logging
import os
import requests
from urlparse import urljoin, urlparse

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import config

_logger = logging.getLogger(__name__)


class DockerRegistry(models.Model):
    _name = 'docker.registry'
    _description = 'Docker Registry'
    _inherit = 'docker.container'
    _directory_prefix = 'registry'

    @api.model
    def _get_default_url(self):
        return config.get('docker_registry_url') or ''

    @api.model
    def _get_default_username(self):
        return config.get('docker_registry_username') or ''

    @api.model
    def _get_default_password(self):
        return config.get('docker_registry_password') or ''

    @api.one
    def _get_images_count(self):
        try:
            self.images_count = len(self.get_images())
        except Exception:
            self.images_count = 0

    name = fields.Char(default='Registry')
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    docker_image = fields.Char(default='registry:2')
    docker_container = fields.Char(
        default='registry', required=True, compute=None)
    auto_run = fields.Boolean(default=True)
    port = fields.Char(required=True, default=5000)
    configfile = fields.Binary(
        'Configuration file', attachment=True, required=True)
    url = fields.Char('URL', required=True, default=_get_default_url)
    username = fields.Char(copy=False, default=_get_default_username)
    password = fields.Char(invisible=True, copy=False,
                           default=_get_default_password)
    images_count = fields.Integer(
        'Images in registry', compute='_get_images_count')
    images = fields.Html('Images in registry', readonly=True)

    _sql_constraints = [
        ('unique_name', 'UNIQUE(docker_container, docker_host_id)',
         'Container name must be unique per docker host'),
        ('unique_port', 'UNIQUE(port, docker_host_id)',
         'Registry port must be unique per docker host'),
    ]

    @api.onchange('docker_host_id', 'port')
    def _onchange_url(self):
        self.url = self._get_url(self.docker_host_id.id, self.port)

    @api.model
    def _get_url(self, docker_host_id, port):
        default_url = self._get_default_url()
        if default_url:
            return default_url
        if not docker_host_id:
            docker_host_id = self._get_default_docker_host()
        base_url = self.env['docker.host'].browse(docker_host_id).base_url
        if base_url.startswith('unix://'):
            scheme = 'http'
            netloc = 'localhost'
        else:
            scheme = urlparse(base_url).scheme
            netloc = urlparse(base_url).netloc
            netloc_wo_auth = netloc.split('@')[-1]
            if ':' in netloc_wo_auth:
                default_port = netloc_wo_auth.split(':')[-1]
                netloc = netloc_wo_auth.replace(':%s' % default_port, '')
        return '%s://%s:%s' % (scheme, netloc, port or 5000)

    @api.multi
    def copy_data(self, default=None):
        default = default or {}
        default['name'] = _('%s copy') % self.name
        default['port'] = int(self.port) + 1
        return super(DockerRegistry, self).copy_data(default)

    @api.model
    def create(self, vals):
        if not vals.get('url'):
            vals['url'] = self._get_url(
                vals.get('docker_host_id'), vals.get('port'))
        registry = super(DockerRegistry, self).create(vals)
        registry.start_container()
        return registry

    @api.multi
    def write(self, vals):
        res = super(DockerRegistry, self).write(vals)
        if 'configfile' in vals:
            for registry in self:
                registry.restart_container()
        if 'url' in vals or 'login' in vals or 'password' in vals:
            for registry in self:
                registry.login()
        return res

    @api.multi
    def unlink(self):
        self._remove_directory()
        return super(DockerRegistry, self).unlink()

    @api.multi
    def _create_configfile(self):
        self.ensure_one()
        filepath = os.path.join(self.build_directory, 'config/config.yml')
        with open(filepath, 'w') as f:
            content = base64.b64decode(self.configfile)
            f.write(content)

    @api.multi
    def _make_directory(self):
        super(DockerRegistry, self)._make_directory()
        dirpaths = [
            os.path.join(self.build_directory, 'config'),
            os.path.join(self.build_directory, 'data'),
        ]
        for dirpath in dirpaths:
            if not os.path.isdir(dirpath):
                os.makedirs(dirpath)
        self._create_configfile()

    @api.multi
    def create_container(self):
        self._make_directory()
        return super(DockerRegistry, self).create_container()

    @api.multi
    def _get_create_container_params(self):
        self.ensure_one()
        params = super(DockerRegistry, self)._get_create_container_params()
        params['host_config'] = {
            'binds': [
                '%s:/etc/docker/registry/config.yml:ro' % os.path.join(
                    self.build_directory, 'config/config.yml'),
                '%s:/var/lib/registry' % os.path.join(
                    self.build_directory, 'data'),
            ],
            'port_bindings': {5000: self.port},
            'restart_policy': {"MaximumRetryCount": 0, "Name": "always"},
            'privileged': True,
        }
        return params

    @api.multi
    def get_registry_image(self, docker_image):
        docker_image = docker_image.split('/')[-1]
        return '%s/%s' % (urlparse(self.url).netloc, docker_image)

    @api.multi
    def login(self):
        self.docker_host_id.login_to_registry(
            self.url, self.username, self.password)
        return True

    @api.multi
    def open(self):
        self.ensure_one()
        if self.username:
            parsed_url = urlparse(self.url)
            url = '%s://%s:%s@%s' % (parsed_url.scheme, self.username,
                                     self.sudo().password, parsed_url.netloc)
        else:
            url = self.url
        return {
            'name': 'Open %s' % self.name,
            'type': 'ir.actions.act_url',
            'url': urljoin(url, 'v2/_catalog?n=1000000'),
            'target': 'new',
        }

    @api.multi
    def remove_image_from_registry(self):
        self.ensure_one()
        return {
            'name': _('Remove image from registry %s') % self.display_name,
            'type': 'ir.actions.act_window',
            'res_model': 'docker.registry.cleaning',
            'view_mode': 'form',
            'view_id': False,
            'context': {'default_docker_registry_id': self.id},
            'target': 'new',
        }

    @api.multi
    def update_images(self):
        self.ensure_one()
        tags_by_image = {}
        images = self.get_images()
        for image in images:
            tags_by_image[image] = sorted(self.get_image_tags(image))
        thead = '<thead><tr><th>Image</th><th>Tags</th></tr></thead>'
        tbody = ''
        for image in sorted(images):
            tbody += '<tr><td>%s</td><td>%s</td></tr>' % (
                image, ', '.join(tags_by_image[image]))
        self.images = '<table class="o_list_view table table-condensed ' \
                      'table-striped">%s%s</table>' % (thead, tbody)
        return True

    @api.multi
    def show_images_in_registry(self):
        self.update_images()
        view = self.env.ref('smile_docker.view_docker_registry_images_form')
        return self.open_wizard(name='Docker Registry Images', view_id=view.id)

    # Python API defined from REST API #

    @api.multi
    def make_request(self, url, headers=None, method='get'):
        self.ensure_one()
        params = {'url': urljoin(self.url, url)}
        if headers:
            params['headers'] = headers
        if self.username:
            params['auth'] = (self.username, self.password)
        return getattr(requests, method)(**params)

    @api.multi
    def get_images(self):
        self.ensure_one()
        url = 'v2/_catalog?n=1000000'
        response = self.make_request(url).json()
        return response.get('repositories') or []

    @api.multi
    def get_image_tags(self, image):
        self.ensure_one()
        url = 'v2/%s/tags/list' % image
        response = self.make_request(url).json()
        return response.get('tags') or []

    @api.multi
    def delete_image(self, image, tag='latest'):
        if tag not in self.get_image_tags(image):
            return True
        _logger.info('Deleting image %s:%s from %s...' %
                     (image, tag, self.docker_container))
        url = 'v2/%s/manifests/%s' % (image, tag)
        headers = {
            'Accept': 'application/vnd.docker.distribution.manifest.v2+json'}
        response = self.make_request(url, headers)
        if response.status_code == 404:  # That means unknow manifest
            return True
        elif response.status_code != 200:
            raise UserError(response.json().get('errors')[0].get('message'))
        digest = response.headers['Docker-Content-Digest']
        url = 'v2/%s/manifests/%s' % (image, digest)
        # Delete manifest (soft delete), ie only marks image tag as deleted
        # and doesn't delete files from file system
        response = self.make_request(url, method='delete')
        if response.status_code == 405:
            raise UserError(_('The image deletion is unsupported. '
                              'Please add the following lines in the registry '
                              'config file\nstorage:\n  delete: true'))
        elif response.status_code != 202:
            raise UserError(response.json().get('errors')[0].get('message'))
        # Delete folder (hard delete)
        params = {
            'container': self.docker_container,
            'cmd': ['bin/registry', 'garbage-collect',
                    '/etc/docker/registry/config.yml'],
        }
        self.docker_host_id.execute_command(**params)
        return True
