# -*- coding: utf-8 -*-

import base64
from functools import wraps
import inspect
import logging
import os
from passlib.hash import bcrypt
import shutil
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
        callers = (frame[3] for frame in inspect.stack())
        if 'preload_registries' not in callers:
            return res
        uid = SUPERUSER_ID
        try:
            env = api.Environment(cr, uid, {})
            if 'docker.registry' in env.registry.models:
                DockerRegistry = env['docker.registry']
                cr.execute("select relname from pg_class where relname='%s'" % DockerRegistry._table)
                if cr.rowcount:
                    _logger.info("Checking registry container is running")
                    for registry in DockerRegistry.search([]):
                        if not registry.is_alive():
                            registry.start_container()
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

    @api.model
    def _get_default_remote_url(self):
        return config.get('registry_remote_url') or ''

    @api.model
    def _get_default_tls_cert(self):
        return config.get('registry_tls_cert') or ''

    @api.model
    def _get_default_tls_key(self):
        return config.get('registry_tls_key') or ''

    @api.one
    def _get_images_count(self):
        self.images_count = len(self.get_images())

    name = fields.Char(required=True, default='registry')
    image = fields.Char(required=True, default='registry:2')
    port = fields.Char(required=True, default=5000)
    configfile = fields.Binary('Configuration file', required=True)
    docker_host_id = fields.Many2one('docker.host', 'Docker host', default=_get_default_docker_host)
    tls_cert = fields.Char('Certificate', default=_get_default_tls_cert)
    tls_key = fields.Char('Key', default=_get_default_tls_key)
    directory = fields.Char(readonly=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    url = fields.Char('URL', required=True)
    remote_url = fields.Char('Remote URL', default=_get_default_remote_url)
    branch_ids = fields.One2many('scm.repository.branch', 'docker_registry_id', 'Branches', readonly=True)
    login = fields.Char(copy=False)
    password = fields.Char(invisible=True, copy=False)
    images_count = fields.Integer('Images in registry', compute='_get_images_count')
    images = fields.Html('Images in registry', readonly=True)

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name, docker_host_id)', 'Registry name must be unique per docker host'),
        ('unique_port', 'UNIQUE(port, docker_host_id)', 'Registry port must be unique per docker host'),
    ]

    @api.multi
    def copy_data(self, default=None):
        default = default or {}
        default['name'] = _('%s copy') % self.name
        return super(DockerRegistry, self).copy_data(default)

    @api.multi
    def get_local_image(self, docker_image):
        docker_image = docker_image.split('/')[-1]
        return '%s/%s' % (urlparse(self.url).netloc, docker_image)

    @api.model
    def _get_default_url(self, vals):
        if config.get('docker_registry_url'):
            return config.get('docker_registry_url')
        vals = vals or {}
        docker_host = vals.get('docker_host_id') or self._get_default_docker_host()
        if isinstance(docker_host, (int, long)):
            docker_host = self.env['docker.host'].browse(docker_host)
        base_url = docker_host.base_url
        tls_cert = vals['tls_cert'] if 'tls_cert' in vals else self._get_default_tls_cert()
        scheme = 'https' if tls_cert else 'http'
        if base_url.startswith('unix://'):
            netloc = 'localhost'
        else:
            netloc = urlparse(base_url).netloc
            netloc_wo_auth = netloc.split('@')[-1]
            if ':' in netloc_wo_auth:
                default_port = netloc_wo_auth.split(':')[-1]
                netloc = netloc_wo_auth.replace(':%s' % default_port, '')
        return '%s://%s:%s' % (scheme, netloc, vals.get('port') or 5000)

    @api.model
    def create(self, vals):
        if 'url' not in vals:
            vals['url'] = self._get_default_url(vals)
        registry = super(DockerRegistry, self).create(vals)
        registry.start_container()
        return registry

    @api.multi
    def write(self, vals):
        res = super(DockerRegistry, self).write(vals)
        if 'configfile' in vals or 'tls_cert' in vals or 'login' in vals:
            for registry in self:
                registry.restart_container()
        return res

    @api.multi
    def unlink(self):
        if self.branch_ids:
            raise UserError(_('You cannot delete a registry linked to branches!'))
        self._remove_directory()
        return super(DockerRegistry, self).unlink()

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
        self._create_htpasswdfile()
        params = self._get_create_container_params()
        _logger.debug(repr(params))
        self._pull_base_image()
        return self.docker_host_id.create_container(**params)

    @api.multi
    def _get_create_container_params(self):
        self.ensure_one()
        binds = [
            '%s:/etc/docker/registry/config.yml:ro' % os.path.join(self.directory, 'config/config.yml'),
            '%s:/var/lib/registry' % os.path.join(self.directory, 'data'),
        ]
        params = {
            'image': self.image,
            'name': self.name,
            'detach': True,
            'ports': [5000],
            'volumes': [
                '/etc/docker/registry/config.yml',
                '/var/lib/registry',
            ],
        }
        if self.tls_cert:
            params['volumes'].append('/certs')
            binds.append('%s:/certs' % os.path.dirname(self.tls_cert))
            params['environment'] = {
                'REGISTRY_HTTP_TLS_CERTIFICATE': os.path.join('/certs', os.path.split(self.tls_cert)[1]),
                'REGISTRY_HTTP_TLS_KEY': os.path.join('/certs', os.path.split(self.tls_key)[1]),
            }
            if self.login:
                params['volumes'].append('/auth/htpasswd')
                binds.append('%s:/auth/htpasswd:ro' % os.path.join(self.directory, 'config/htpasswd'))
                params['environment'].update({
                    'REGISTRY_AUTH': 'htpasswd',
                    'REGISTRY_AUTH_HTPASSWD_REALM': 'Registry Realm',
                    'REGISTRY_AUTH_HTPASSWD_PATH': '/auth/htpasswd',
                })
        params['host_config'] = self.docker_host_id.create_host_config(
            binds=binds,
            port_bindings={5000: self.port},
            restart_policy={"MaximumRetryCount": 0, "Name": "always"},
            privileged=True,
        )
        return params

    @api.multi
    def auth_config(self):
        self.ensure_one()
        config = {'insecure_registry': not self.url.startswith('https')}
        if self.login:
            config['auth_config'] = {
                'username': self.login,
                'password': self.sudo().password,
            }
        return config

    @api.multi
    def _pull_base_image(self):
        kwargs = self.auth_config()
        self.docker_host_id.pull_image(self.image, **kwargs)

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
    def _create_htpasswdfile(self):
        self.ensure_one()
        filepath = os.path.join(self.directory, 'config/htpasswd')
        with open(filepath, 'w') as f:
            if self.login and self.sudo().password:
                f.write('%s:%s' % (self.login, bcrypt.encrypt(self.sudo().password)))

    @api.multi
    def _create_directory(self):
        self.ensure_one()
        registry_path = os.path.join(self.docker_host_id.registries_path, str(self.id))
        dirpaths = [
            registry_path,
            os.path.join(registry_path, 'config'),
            os.path.join(registry_path, 'data'),
        ]
        for dirpath in dirpaths:
            if not os.path.isdir(dirpath):
                os.makedirs(dirpath)
        self.directory = registry_path

    @api.one
    def _remove_directory(self):
        if self.directory and os.path.exists(self.directory):
            shutil.rmtree(self.directory)

    @api.multi
    def _get_headers(self):
        if self.login:
            header = "{'username': %s, 'password': %s}" % (self.login, self.sudo().password)
            return {"X-Registry-Auth": base64.urlsafe_b64encode(header)}
        return {}

    @api.multi
    def get_images(self):
        self.ensure_one()
        url = urljoin(self.url, 'v2/_catalog')
        return requests.get(url, headers=self._get_headers()).json().get('repositories') or []

    @api.multi
    def get_image_tags(self, image):
        self.ensure_one()
        if image not in self.get_images():
            return []
        url = urljoin(self.url, 'v2/%s/tags/list' % image)
        return requests.get(url, headers=self._get_headers()).json().get('tags') or []

    @api.multi
    def delete_image(self, image, tag='latest'):
        if tag not in self.get_image_tags(image):
            return True
        _logger.info('Deleting image %s:%s from %s...' % (image, tag, self.name))
        url = urljoin(self.url, 'v2/%s/manifests/%s' % (image, tag))
        headers = {'Accept': 'application/vnd.docker.distribution.manifest.v2+json'}
        headers.update(self._get_headers())
        response = requests.get(url, headers=headers)
        if response.status_code == 404:  # That means unknow manifest
            return True
        elif response.status_code != 200:
            raise UserError(response.json().get('errors')[0].get('message'))
        digest = response.headers['Docker-Content-Digest']
        url = urljoin(self.url, 'v2/%s/manifests/%s' % (image, digest))
        # Delete manifest (soft delete), ie only marks image tag as deleted and doesn't delete files from file system
        response = requests.delete(url, headers=self._get_headers())
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
        return {
            'name': 'Open %s' % self.name,
            'type': 'ir.actions.act_url',
            'url': urljoin(self.remote_url or self.url, 'v2/_catalog'),
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
