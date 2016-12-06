# -*- coding: utf-8 -*-

import logging
import os.path
import tempfile
from urlparse import urljoin, urlparse

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import config

from ..tools import b2human, get_exception_message
from ..tools.docker_api import Client, TLSConfig

_logger = logging.getLogger(__name__)


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
            base_url = config.get('build_base_url')
        else:
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        netloc = urlparse(base_url).netloc
        port = netloc.split(':')[-1]
        netloc = netloc.replace(':%s' % port, '')
        return urljoin(base_url, '//%s' % netloc)

    @api.model
    def _get_default_redirect_subdomain_to_port(self):
        return config.get('redirect_subdomain_to_port') or False

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
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    builds_host_config = fields.Text()
    stats = fields.Html("Last stats", readonly=True)
    stats_date = fields.Datetime("Stats date", readonly=True)
    stats_containers = fields.Integer("Running containers", readonly=True)

    @property
    def builds_path(self):
        dirpath = config.get('builds_path') or tempfile.gettempdir()
        if not os.path.isdir(dirpath):
            raise UserError(_("%s doesn't exist or is not a directory") % dirpath)
        return dirpath

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

    @api.multi
    def get_build_url(self, port):
        self.ensure_one()
        netloc = urlparse(self.build_base_url).netloc
        if self.redirect_subdomain_to_port:
            # Add subdomain
            auth = ''
            if '@' in netloc:
                auth, netloc = netloc.split('@')
                auth += '@'
            if netloc.startswith('www.'):
                netloc.replace('www.', '')
            return urljoin(self.build_base_url, '//%sbuild_%s.%s' % (auth, port, netloc))
        # Replace default port
        netloc_wo_auth = netloc.split('@')[-1]
        if ':' in netloc_wo_auth:
            default_port = netloc_wo_auth.split(':')[-1]
            netloc = netloc_wo_auth.replace(':%s' % default_port, '')
        return urljoin(self.build_base_url, '//%s:%s' % (netloc, port))

    @api.multi
    def update_stats(self):
        self.ensure_one()
        data = {}
        containers = self.get_containers()
        container_names = map(lambda cont: cont['Names'][0].replace('/', ''), containers)
        for container in container_names:
            stats_gen = self.get_stats(container, decode=True)
            pre_stats = stats_gen.next()
            stats = stats_gen.next()
            data[container] = [
                '%.2f %%' % ((stats['cpu_stats']['cpu_usage']['total_usage'] -
                              pre_stats['cpu_stats']['cpu_usage']['total_usage']) * 100.0 /
                             (stats['cpu_stats']['system_cpu_usage'] - pre_stats['cpu_stats']['system_cpu_usage'])),
                '%s / %s' % (b2human(stats['memory_stats']['usage']),
                             b2human(stats['memory_stats']['limit'])),
                '%.2f %%' % (stats['memory_stats']['usage'] * 100.0 / stats['memory_stats']['limit']),
                '%.2f %%' % (stats['memory_stats']['max_usage'] * 100.0 / stats['memory_stats']['limit']),
                '%s / %s' % (b2human(sum(network['rx_bytes'] for network in stats['networks'].itervalues())),
                             b2human(sum(network['tx_bytes'] for network in stats['networks'].itervalues()))),
            ]
        thead = """
<thead>
    <tr>
        <th>CONTAINER</th>
        <th>CPU %</th>
        <th>MEM USAGE / LIMIT</th>
        <th>MEM %</th>
        <th>MAX %</th>
        <th>NETWORK I/O</th>
    </tr>
</thead>"""
        tbody = ''
        for container in sorted(container_names):
            tbody += '<tr><td>%s</td>%s</tr>' \
                % (container, ''.join(map(lambda value: '<td>%s</td>' % value, data[container])))
        self.stats = '<table class="o_list_view table table-condensed table-striped">%s%s</table>' % (thead, tbody)
        self.stats_containers = len(container_names)
        self.stats_date = fields.Datetime.now()
        return True

    @api.multi
    def show_current_stats(self):
        self.update_stats()
        view = self.env.ref('smile_ci.view_docker_host_stats_form')
        return self.open_wizard(name='Docker Host Stats', view_id=view.id)

    @api.multi
    def _show_history_stats(self, view_mode):
        self.ensure_one()
        return {
            'name': _('Docker Host Stats'),
            'type': 'ir.actions.act_window',
            'res_model': 'docker.host.stats',
            'view_type': 'form',
            'view_mode': view_mode,
            'domain': [('docker_host_id', '=', self.id)],
            'target': 'new',
        }

    @api.multi
    def show_history_stats_as_pivot(self):
        return self._show_history_stats('pivot')

    @api.multi
    def show_history_stats_as_graph(self):
        return self._show_history_stats('graph')

    # Client #

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
                elif self.tls_verify and self.tls_cert:
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

    # Host #

    @api.multi
    def get_host_info(self):
        self.ensure_one()
        _logger.info('Getting infos for host %s...' % self.display_name)
        return self.client.info()

    # Container #

    @api.multi
    def get_containers(self, *args, **kwargs):
        _logger.debug(repr(kwargs))
        containers = []
        for docker_host in self:
            containers.extend(docker_host.client.containers(**kwargs))
        return containers

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
        try:
            self.client.start(container)
        except Exception, e:
            raise UserError(_("Starting container %s failed\n\n%s") % (container, get_exception_message(e)))
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
    def remove_container(self, container, **kwargs):
        self.ensure_one()
        _logger.info('Removing container %s...' % container)
        # When we filter by name, we search if name contains search operand
        # So we need to filter manually search results
        containers = self.get_containers(all=True, filters={'name': container})
        containers = map(lambda container: container['Names'][0].replace('/', ''), containers)
        if 'v' not in kwargs:
            kwargs['v'] = True
        if container in containers:
            kwargs['container'] = container
            _logger.debug(repr(kwargs))
            self.client.remove_container(**kwargs)
        return True

    @api.multi
    def execute_command(self, container, cmd, **kwargs):
        self.ensure_one()
        command = cmd
        if isinstance(cmd, list):
            cmd = map(str, cmd)
            command = ' '.join(cmd)
        _logger.info('Executing command %s inside container %s...'
                     % (command, container))
        kwargs['container'] = container
        kwargs['cmd'] = cmd
        _logger.debug(repr(kwargs))
        cli = self.client
        if getattr(cli, 'exec_create', False):
            exec_id = cli.exec_create(**kwargs)
            return cli.exec_start(exec_id)
        # The command 'execute' is deprecated for docker-py >= 1.2.0
        return cli.execute(**kwargs)

    @api.multi
    def get_archive(self, container, path):
        self.ensure_one()
        _logger.info('Retrieving %s from container %s...' % (path, container))
        strm, stat = self.client.get_archive(container, path)
        _logger.debug(stat)
        return strm

    @api.multi
    def get_stats(self, container, **kwargs):
        self.ensure_one()
        _logger.info('Getting stats for container %s...' % container)
        kwargs['container'] = container
        _logger.debug(repr(kwargs))
        return self.client.stats(**kwargs)

    @api.multi
    def get_logs(self, container, **kwargs):
        self.ensure_one()
        _logger.info('Getting logs for container %s...' % container)
        kwargs['container'] = container
        _logger.debug(repr(kwargs))
        return self.client.logs(**kwargs)

    @api.multi
    def get_running_processes(self, container, **kwargs):
        self.ensure_one()
        _logger.info('Getting running processes for container %s...' % container)
        kwargs['container'] = container
        _logger.debug(repr(kwargs))
        return self.client.top(**kwargs)

    # Image #

    @api.multi
    def get_images(self, *args, **kwargs):
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
            raise UserError(_("Building image %s failed\n\n%s") % (tag, all_lines[-1]['error']))
        return '\n'.join(map(str, all_lines))

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
    def tag_image(self, image, tags=None, **kwargs):
        self.ensure_one()
        tags = tags or 'latest'
        if isinstance(tags, basestring):
            tags = [tags]
        kwargs['image'] = image
        for tag in tags:
            new_tag = '%s:%s' % (kwargs['repository'], tag) \
                      if kwargs.get('repository') else tag
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

    @api.one
    def _purge_images(self):
        _logger.info('Purging unused images for %s...' % self.display_name)
        for image in self.client.images(quiet=True, filters={'dangling': True}):
            self.client.remove_image(image, force=True)

    @api.model
    def purge_images(self):
        self.search([])._purge_images()
        return True

    # Network #

    @api.multi
    def get_networks(self, *args, **kwargs):
        self.ensure_one()
        _logger.debug(repr(kwargs))
        return self.client.networks(**kwargs)

    @api.multi
    def create_network(self, network, **kwargs):
        self.ensure_one()
        _logger.info('Creating network %s...' % network)
        kwargs['name'] = network
        if 'driver' not in kwargs:
            kwargs['driver'] = 'bridge'
        _logger.debug(repr(kwargs))
        return self.client.create_network(**kwargs)

    @api.multi
    def remove_network(self, network):
        self.ensure_one()
        _logger.info('Removing network %s...' % network)
        _logger.debug(network)
        if self.get_networks([network]):
            self.client.remove_network(network)
        return True

    # Registry #

    @api.multi
    def login_to_registry(self, registry, username, password, **kwargs):
        self.ensure_one()
        _logger.info('Logging in to registry %s with username %s...' % (registry, username))
        kwargs.update({
            'registry': registry,
            'username': username,
            'password': password,
        })
        if 'reauth' not in kwargs:
            kwargs['reauth'] = True
        _logger.debug(repr(kwargs))
        return self.client.login(**kwargs)

    # Volume #

    @api.multi
    def get_volumes(self, *args, **kwargs):
        self.ensure_one()
        _logger.debug(repr(kwargs))
        return self.client.volumes(**kwargs)

    @api.multi
    def create_volume(self, volume, **kwargs):
        self.ensure_one()
        _logger.info('Creating volume %s...' % volume)
        kwargs['name'] = volume
        if 'driver' not in kwargs:
            kwargs['driver'] = 'local'
        _logger.debug(repr(kwargs))
        return self.client.create_volume(**kwargs)

    @api.multi
    def remove_volume(self, volume):
        self.ensure_one()
        _logger.info('Removing volume %s...' % volume)
        _logger.debug(volume)
        if self.get_volumes([volume]):
            self.client.remove_volume(volume)
        return True

    # Utils #

    @api.multi
    def create_host_config(self, *args, **kwargs):
        self.ensure_one()
        return self.client.create_host_config(**kwargs)

    @api.multi
    def create_networking_config(self, *args, **kwargs):
        self.ensure_one()
        return self.client.create_networking_config(*args, **kwargs)

    @api.multi
    def create_endpoint_config(self, *args, **kwargs):
        self.ensure_one()
        return self.client.create_endpoint_config(**kwargs)
