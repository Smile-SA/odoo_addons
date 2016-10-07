# -*- coding: utf-8 -*-

import logging
import os.path
import tempfile
from urlparse import urljoin, urlparse

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import config

_logger = logging.getLogger(__name__)


try:
    from docker import Client
    from docker.tls import TLSConfig
except ImportError:
    _logger.warning("Please install docker package")


class DockerHost(models.Model):
    _name = 'docker.host'
    _description = 'Docker Host'
    _rec_name = 'base_url'

    @api.model
    def _get_default_base_url(self):
        return config.get('docker_base_url') or 'unix://var/run/docker.sock'

    @api.model
    def _get_default_version(self):
        return config.get('docker_version') or ''

    @api.model
    def _get_default_tls(self):
        return config.get('docker_tls') or False

    @api.model
    def _get_default_build_base_url(self):
        if config.get('build_base_url'):
            return config.get('build_base_url')
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        netloc = urlparse(base_url).netloc
        port = netloc.split(':')[-1]
        netloc = netloc.replace(':%s' % port, '')
        return urljoin(base_url, '//%s' % netloc)

    @api.model
    def _get_default_remote_build_base_url(self):
        return config.get('remote_build_base_url') or ''

    @api.model
    def _get_default_redirect_subdomain_to_port(self):
        return config.get('docker_redirect_subdomain_to_port') or False

    @api.model
    def _get_default_remote_redirect_subdomain_to_port(self):
        return config.get('remote_redirect_subdomain_to_port') or False

    @api.model
    def _get_default_path(self, config_option):
        default_path = config_option and config.get(config_option) or tempfile.gettempdir()
        if not os.path.isdir(default_path):
            try:
                os.mkdir(default_path)
            except:
                raise UserError(_("Permission denied to create the directory named %s") % default_path)
        return default_path

    @api.model
    def _get_default_builds_path(self):
        return self._get_default_path('builds_path')

    @api.model
    def _get_default_registries_path(self):
        return self._get_default_path('registries_path')

    base_url = fields.Char(required=True, default=_get_default_base_url)
    version = fields.Char('API version', default=_get_default_version)
    timeout = fields.Integer(default=60, help='In seconds')
    tls = fields.Boolean(default=_get_default_tls)
    tls_verify = fields.Boolean('Verify', default=True)
    tls_ca_cert = fields.Char('CA certificate')
    tls_cert = fields.Char('Client certificate')
    tls_key = fields.Char('Client key')
    build_base_url = fields.Char(required=True, default=_get_default_build_base_url)
    redirect_subdomain_to_port = fields.Boolean(default=_get_default_redirect_subdomain_to_port)
    remote_build_base_url = fields.Char(default=_get_default_remote_build_base_url)
    remote_redirect_subdomain_to_port = fields.Boolean(default=_get_default_remote_redirect_subdomain_to_port)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    builds_path_store = fields.Char('Builds path', required=True, default=_get_default_builds_path)
    registries_path_store = fields.Char('Registries path', required=True,
                                        default=_get_default_registries_path)

    @api.model
    def _check_path(self, dirpath):
        if not os.path.isdir(dirpath):
            raise UserError(_("%s doesn't exist or is not a directory") % dirpath)
        return dirpath

    @property
    def builds_path(self):
        return self._check_path(self.builds_path_store)

    @property
    def registries_path(self):
        return self._check_path(self.registries_path_store)

    @api.model
    def get_default_docker_host(self):
        docker_hosts = self.search([])
        if not docker_hosts:
            raise UserError(_('No docker host is configured'))
        default_docker_host = docker_hosts[0]
        if len(docker_hosts) > 1:
            min_containers_nb = len(default_docker_host.get_containers())
            for docker_host in docker_hosts[1:]:
                containers_nb = len(docker_host.get_containers())
                if containers_nb < min_containers_nb:
                    default_docker_host = docker_host
        return default_docker_host

    _clients = {}

    @property
    def client(self):
        if self.id not in self._clients:
            kwargs = {
                'base_url': self.base_url,
                'tls': self.tls,
                'timeout': self.timeout,
            }
            if self.version:
                kwargs['version'] = self.version
            if self.tls and (not self.tls_verify or self.tls_ca_cert or self.tls_cert):
                if not self.tls_verify and not self.tls_cert:
                    tls_params = {'verify': False}
                elif not self.tls_verify and self.tls_cert:
                    tls_params = {'client_cert': (self.tls_cert, self.tls_key)}
                elif self.tls_verify and not self.tls_cert:
                    tls_params = {'ca_cert': self.tls_ca_cert}
                elif self.tls_verify and not self.tls_cert:
                    tls_params = {
                        'client_cert': (self.tls_cert, self.tls_key),
                        'verify': self.tls_ca_cert,
                    }
                tls_config = TLSConfig(**tls_params)
                kwargs['tls'] = tls_config
            self._clients[self.id] = Client(**kwargs)
        return self._clients[self.id]

    @api.multi
    def write(self, vals):
        for docker_host_id in self.ids:
            self._clients.pop(docker_host_id, None)
        return super(DockerHost, self).write(vals)

    @api.multi
    def get_containers(self, **kwargs):
        _logger.debug(repr(kwargs))
        containers = []
        for docker_host in self:
            containers.extend(docker_host.client.containers(**kwargs))
        return containers

    @api.multi
    def get_images(self, **kwargs):
        _logger.debug(repr(kwargs))
        containers = []
        for docker_host in self:
            containers.extend(docker_host.client.images(**kwargs))
        return containers

    @api.multi
    def build_image(self, path, tag, **kwargs):
        self.ensure_one()
        _logger.info('Building image %s...' % tag)
        kwargs.update({
            'path': path,
            'tag': tag,
            'forcerm': True,
            'decode': True,
        })
        _logger.debug(repr(kwargs))
        generator = self.client.build(**kwargs)
        all_lines = []
        for line in generator:
            all_lines.append(line)
            _logger.debug(line)
        if 'Successfully built' not in all_lines[-1].get('stream', ''):
            self.purge_images()
            raise UserError(repr(all_lines[-1]['error']))
        return '\n'.join(map(str, all_lines))

    @api.multi
    def create_host_config(self, **kwargs):
        self.ensure_one()
        _logger.debug(repr(kwargs))
        return self.client.create_host_config(**kwargs)

    @api.multi
    def create_container(self, image, name, **kwargs):
        self.ensure_one()
        _logger.info('Creating container %s...' % name)
        kwargs.update({
            'image': image,
            'name': name,
        })
        _logger.debug(repr(kwargs))
        return self.client.create_container(**kwargs)

    @api.multi
    def start_container(self, container):
        self.ensure_one()
        _logger.info('Starting container %s...' % container)
        response = self.client.start(container)
        if response:
            raise UserError(response)
        return True

    @api.multi
    def remove_container(self, container, **kwargs):
        self.ensure_one()
        _logger.info('Removing container %s...' % container)
        # When we filter by name, we search if name contains search operand
        # So we need to filter manually search results
        containers = self.get_containers(all=True, filters={'name': container})
        containers = map(lambda container: container['Names'][0].replace('/', ''), containers)
        if container in containers:
            kwargs['container'] = container
            _logger.debug(repr(kwargs))
            self.client.remove_container(**kwargs)
        return True

    @api.multi
    def commit_container(self, container, repository, **kwargs):
        self.ensure_one()
        _logger.info('Creating image %s from container %s...'
                     % (repository, container))
        kwargs.update({
            'container': container,
            'repository': repository,
        })
        _logger.debug(repr(kwargs))
        self.client.commit(**kwargs)
        return True

    @api.multi
    def tag_image(self, image, tags='latest', **kwargs):
        self.ensure_one()
        if isinstance(tags, basestring):
            tags = [tags]
        kwargs['image'] = image
        for tag in tags:
            new_tag = '%s:%s' % (kwargs['repository'], tag) \
                      if 'repository' in kwargs else tag
            _logger.info('Tagging image %s as %s...' % (image, new_tag))
            kwargs['tag'] = tag
            _logger.debug(repr(kwargs))
            self.client.tag(**kwargs)
        return True

    @api.multi
    def push_image(self, repository, **kwargs):
        self.ensure_one()
        _logger.info('Pushing image %s...' % repository)
        kwargs['repository'] = repository
        _logger.debug(repr(kwargs))
        return self.client.push(**kwargs)

    @api.multi
    def remove_image(self, image, **kwargs):
        self.ensure_one()
        _logger.info('Removing image %s...' % image)
        if self.client.images(name=image, all=True):
            kwargs['image'] = image
            _logger.debug(repr(kwargs))
            self.client.remove_image(**kwargs)
        return True

    @api.multi
    def get_logs(self, container, **kwargs):
        self.ensure_one()
        kwargs['container'] = container
        _logger.debug(repr(kwargs))
        return self.client.logs(**kwargs)

    @api.multi
    def get_archive(self, container, path):
        self.ensure_one()
        _logger.info('Retrieving %s from container %s...' % (path, container))
        strm, stat = self.client.get_archive(container, path)
        _logger.debug(stat)
        return strm

    @api.multi
    def pull_image(self, repository, **kwargs):
        self.ensure_one()
        _logger.info('Pulling image %s...' % repository)
        for image in self.client.images(all=True):
            if repository in (image.get('RepoTags') or []):
                return image
        tag = repository.split('/')[-1].split(':')[-1]
        repository = repository[:-len(tag) - 1]
        return self.client.pull(repository, tag, **kwargs)

    @api.multi
    def execute_command(self, container, cmd, **kwargs):
        self.ensure_one()
        _logger.info('Executing command %s inside container %s...' % (cmd, container))
        kwargs['container'] = container
        kwargs['cmd'] = cmd
        _logger.debug(repr(kwargs))
        cli = self.client
        if getattr(cli, 'exec_create', False):
            exec_id = cli.exec_create(**kwargs)['Id']
            cli.exec_start(exec_id)
        else:  # The command 'execute' is deprecated for docker-py >= 1.2.0
            cli.execute(**kwargs)
        return True

    @api.one
    def _purge_images(self):
        _logger.info('Purging unused images for %s...' % self.base_url)
        for image in self.client.images(quiet=True, filters={'dangling': True}):
            self.client.remove_image(image, force=True)

    @api.model
    def purge_images(self):
        self.search([])._purge_images()
        return True

    @api.multi
    def get_build_url(self, port, remote=False):
        self.ensure_one()
        if remote:
            base_url = self.remote_build_base_url
            redirect_subdomain_to_port = self.remote_redirect_subdomain_to_port
        else:
            base_url = self.build_base_url
            redirect_subdomain_to_port = self.redirect_subdomain_to_port
        netloc = urlparse(base_url).netloc
        if redirect_subdomain_to_port:
            # Add subdomain
            auth = ''
            if '@' in netloc:
                auth, netloc = netloc.split('@')
                auth += '@'
            if netloc.startswith('www.'):
                netloc.replace('www.', '')
            return urljoin(base_url, '//%sbuild_%s.%s' % (auth, port, netloc))
        # Replace default port
        netloc_wo_auth = netloc.split('@')[-1]
        if ':' in netloc_wo_auth:
            default_port = netloc_wo_auth.split(':')[-1]
            netloc = netloc_wo_auth.replace(':%s' % default_port, '')
        return urljoin(base_url, '//%s:%s' % (netloc, port))
