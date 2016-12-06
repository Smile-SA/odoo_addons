# -*- coding: utf-8 -*-

import base64
from functools import wraps
import inspect
import logging
import os
import shutil
from threading import Thread
from urlparse import urljoin, urlparse

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.modules.registry import Registry
from odoo.tools import config

from ..tools import get_exception_message

_logger = logging.getLogger(__name__)

try:
    from docker.errors import APIError
except ImportError:
    _logger.warning("Please install docker package")

try:
    import requests
except ImportError:
    _logger.warning("Please install requests package")


def registry_start(setup_models):
    @wraps(setup_models)
    def new_setup_models(self, cr, *args, **kwargs):
        res = setup_models(self, cr, *args, **kwargs)
        callers = [frame[3] for frame in inspect.stack()]
        if 'preload_registries' not in callers:
            return res
        try:
            env = api.Environment(cr, SUPERUSER_ID, {})
            if 'docker.registry' in env.registry.models:
                DockerRegistry = env['docker.registry']
                cr.execute("select relname from pg_class where relname='%s'" % DockerRegistry._table)
                if cr.rowcount:
                    registries = DockerRegistry.search([])
                    # Empty builds directory except for pending builds
                    directories = registries.mapped('directory')
                    builds_path = env['docker.host'].builds_path
                    for dirname in os.listdir(builds_path):
                        dirpath = os.path.join(builds_path, dirname)
                        if dirname.startswith('registry_') and dirpath not in directories:
                            _logger.info('Removing %s' % dirpath)
                            thread = Thread(target=shutil.rmtree, args=(dirpath,))
                            thread.start()
                    # Start registry container if not running
                    _logger.info("Checking registry container is running")
                    for registry in registries:
                        if not registry.is_alive():
                            registry.start_container()
                        registry.login()
        except Exception, e:
            _logger.error(get_exception_message(e))
        return res
    return new_setup_models


class DockerRegistry(models.Model):
    _name = 'docker.registry'
    _description = 'Docker Registry'

    def __init__(self, pool, cr):
        super(DockerRegistry, self).__init__(pool, cr)
        setattr(Registry, 'setup_models', registry_start(getattr(Registry, 'setup_models')))

    @api.model
    def _get_default_docker_host(self):
        docker_hosts = self.env['docker.host'].search([])
        if not docker_hosts:
            raise UserError(_('No docker host is configured'))
        return docker_hosts[0].id

    @api.one
    def _get_directory(self):
        self.directory = os.path.join(self.docker_host_id.builds_path, 'registry_%s' % self.id)

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
        self.images_count = len(self.get_images())

    name = fields.Char(required=True, default='registry')
    docker_image = fields.Char(required=True, default='registry:2')
    port = fields.Char(required=True, default=5000)
    configfile = fields.Binary('Configuration file', required=True)
    docker_host_id = fields.Many2one('docker.host', 'Docker host', default=_get_default_docker_host)
    directory = fields.Char(compute='_get_directory')
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    url = fields.Char('URL', required=True, default=_get_default_url)
    branch_ids = fields.One2many('scm.repository.branch', 'docker_registry_id', 'Branches', readonly=True)
    username = fields.Char(copy=False, default=_get_default_username)
    password = fields.Char(invisible=True, copy=False, default=_get_default_password)
    images_count = fields.Integer('Images in registry', compute='_get_images_count')
    images = fields.Html('Images in registry', readonly=True)

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name, docker_host_id)', 'Registry name must be unique per docker host'),
        ('unique_port', 'UNIQUE(port, docker_host_id)', 'Registry port must be unique per docker host'),
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
        return super(DockerRegistry, self).copy_data(default)

    @api.multi
    def get_registry_image(self, docker_image):
        docker_image = docker_image.split('/')[-1]
        return '%s/%s' % (urlparse(self.url).netloc, docker_image)

    @api.model
    def create(self, vals):
        if not vals.get('url'):
            vals['url'] = self._get_url(vals.get('docker_host_id'), vals.get('port'))
        registry = super(DockerRegistry, self).create(vals)
        registry.start_container()
        registry.login()
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
        if self.branch_ids:
            raise UserError(_('You cannot delete a registry linked to branches!'))
        self._remove_directory()
        return super(DockerRegistry, self).unlink()

    @api.multi
    def login(self):
        self.ensure_one()
        if self.username:
            for docker_host in self.env['docker.host'].search([]):
                docker_host.login_to_registry(self.url, self.username, self.password)
        return True

    @api.multi
    def is_alive(self, all=False):
        self.ensure_one()
        if self.docker_host_id.get_containers(all=all, filters={'name': self.name}):
            return self.name
        return False

    @api.multi
    def _create_container(self):
        self.ensure_one()
        _logger.info('Creating container %s...' % self.name)
        self._create_directory()
        self._create_configfile()
        params = self._get_create_container_params()
        _logger.debug(repr(params))
        self.docker_host_id.pull_image(self.docker_image)
        return self.docker_host_id.create_container(**params)

    @api.multi
    def _get_create_container_params(self):
        self.ensure_one()
        host_config = self.docker_host_id.create_host_config(
            binds=[
                '%s:/etc/docker/registry/config.yml:ro' % os.path.join(self.directory, 'config/config.yml'),
                '%s:/var/lib/registry' % os.path.join(self.directory, 'data'),
            ],
            port_bindings={5000: self.port},
            restart_policy={"MaximumRetryCount": 0, "Name": "always"},
            privileged=True,
        )
        return {
            'image': self.docker_image,
            'name': self.name,
            'detach': True,
            'ports': [5000],
            'volumes': [
                '/etc/docker/registry/config.yml',
                '/var/lib/registry',
            ],
            'host_config': host_config,
        }

    @api.multi
    def start_container(self):
        container = self.is_alive(all=True)
        if not container:
            container = self._create_container()
        _logger.info('Starting container %s and expose it in port %s...' % (self.name, self.port))
        self.docker_host_id.start_container(container)
        return True

    @api.multi
    def stop_container(self):
        _logger.info('Removing container %s...' % self.name)
        self.ensure_one()
        try:
            if self.is_alive(all=True):
                self.docker_host_id.remove_container(self.name, force=True)
        except APIError, e:
            _logger.warning(e)
        return True

    @api.multi
    def restart_container(self):
        self.stop_container()
        return self.start_container()

    @api.multi
    def _create_configfile(self):
        self.ensure_one()
        filepath = os.path.join(self.directory, 'config/config.yml')
        with open(filepath, 'w') as f:
            content = base64.b64decode(self.configfile)
            f.write(content)

    @api.multi
    def _create_directory(self):
        self.ensure_one()
        dirpaths = [
            self.directory,
            os.path.join(self.directory, 'config'),
            os.path.join(self.directory, 'data'),
        ]
        for dirpath in dirpaths:
            if not os.path.isdir(dirpath):
                os.makedirs(dirpath)

    @api.one
    def _remove_directory(self):
        if self.directory and os.path.exists(self.directory):
            shutil.rmtree(self.directory)

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
        url = 'v2/_catalog'
        response = self.make_request(url).json()
        return response.get('repositories') or []

    @api.multi
    def get_image_tags(self, image):
        self.ensure_one()
        if image not in self.get_images():
            return []
        url = 'v2/%s/tags/list' % image
        response = self.make_request(url).json()
        return response.get('tags') or []

    @api.multi
    def delete_image(self, image, tag='latest'):
        if tag not in self.get_image_tags(image):
            return True
        _logger.info('Deleting image %s:%s from %s...' % (image, tag, self.name))
        url = 'v2/%s/manifests/%s' % (image, tag)
        headers = {'Accept': 'application/vnd.docker.distribution.manifest.v2+json'}
        response = self.make_request(url, headers)
        if response.status_code == 404:  # That means unknow manifest
            return True
        elif response.status_code != 200:
            raise UserError(response.json().get('errors')[0].get('message'))
        digest = response.headers['Docker-Content-Digest']
        url = 'v2/%s/manifests/%s' % (image, digest)
        # Delete manifest (soft delete), ie only marks image tag as deleted and doesn't delete files from file system
        response = self.make_request(url, method='delete')
        if response.status_code == 405:
            raise UserError(_('The image deletion is unsupported. '
                              'Please add the following lines in the registry config file\nstorage:\n  delete: true'))
        elif response.status_code != 202:
            raise UserError(response.json().get('errors')[0].get('message'))
        # Delete folder (hard delete)
        params = self._get_execute_command_params()
        self.docker_host_id.execute_command(**params)
        return True

    @api.multi
    def _get_execute_command_params(self):
        self.ensure_one()
        return {
            'container': self.name,
            'cmd': ['bin/registry', 'garbage-collect', '/etc/docker/registry/config.yml'],
        }

    @api.multi
    def open(self):
        self.ensure_one()
        if self.username:
            parsed_url = urlparse(self.url)
            url = '%s://%s:%s@%s' % (parsed_url.scheme, self.username, self.sudo().password, parsed_url.netloc)
        else:
            url = self.url
        return {
            'name': 'Open %s' % self.name,
            'type': 'ir.actions.act_url',
            'url': urljoin(url, 'v2/_catalog'),
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
            tbody += '<tr><td>%s</td><td>%s</td></tr>' % (image, ', '.join(tags_by_image[image]))
        self.images = '<table class="o_list_view table table-condensed table-striped">%s%s</table>' % (thead, tbody)
        return True

    @api.multi
    def show_images_in_registry(self):
        self.update_images()
        view = self.env.ref('smile_ci.view_docker_registry_images_form')
        return self.open_wizard(name='Docker Registry Images', view_id=view.id)
