# -*- coding: utf-8 -*-

from distutils.version import LooseVersion
import docker
from docker.tls import TLSConfig
import logging
import os.path
from six import string_types
import tempfile

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import config

from ..tools import b2human, format_repository, \
    format_repository_and_tag, get_exception_message

if LooseVersion(docker.version) < '1.5.0':
    raise ImportError("Please install a version of docker >= '1.5.0'")

try:
    from docker import APIClient as Client  # Docker SDK for Python >= 2.0
except ImportError:
    from docker import Client

_logger = logging.getLogger(__name__)


class DockerHost(models.Model):
    _name = 'docker.host'
    _description = 'Docker Host'
    _rec_name = 'base_url'
    _order = 'sequence'

    @api.model
    def _get_default_base_url(self):
        return config.get('docker_base_url') or 'unix://var/run/docker.sock'

    @api.model
    def _get_default_version(self):
        return config.get('docker_version') or ''

    @api.model
    def _get_default_tls(self):
        return config.get('docker_tls') or False

    base_url = fields.Char(required=True, default=_get_default_base_url)
    version = fields.Char('API version', default=_get_default_version)
    timeout = fields.Integer(default=60, help='In seconds')
    tls = fields.Boolean(default=_get_default_tls)
    tls_verify = fields.Boolean('Verify', default=True)
    tls_ca_cert = fields.Char('CA certificate')
    tls_cert = fields.Char('Client certificate')
    tls_key = fields.Char('Client key')
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    stats = fields.Html("Last stats", readonly=True)
    stats_date = fields.Datetime("Stats date", readonly=True)
    stats_containers = fields.Integer("Running containers", readonly=True)

    @property
    def builds_path(self):
        dirpath = config.get('builds_path') or tempfile.gettempdir()
        if not os.path.isdir(dirpath):
            raise UserError(_("%s doesn't exist or is not a directory")
                            % dirpath)
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
            if self.tls and (not self.tls_verify or
                             self.tls_ca_cert or self.tls_cert):
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
        _logger.debug('Getting infos for host %s...' % self.display_name)
        return self.client.info()

    # Registry #

    @api.multi
    def login_to_registry(self, registry, username, password, **kwargs):
        self.ensure_one()
        _logger.info('Logging in to registry %s with username %s...'
                     % (registry, username))
        kwargs.update({
            'registry': registry,
            'username': username,
            'password': password,
        })
        if 'reauth' not in kwargs:
            kwargs['reauth'] = True
        _logger.debug(repr(kwargs))
        return self.client.login(**kwargs)

    # Utils #

    @api.multi
    def _create_host_config(self, *args, **kwargs):
        self.ensure_one()
        return self.client.create_host_config(**kwargs)

    @api.multi
    def _create_networking_config(self, *args, **kwargs):
        self.ensure_one()
        return self.client.create_networking_config(*args, **kwargs)

    @api.multi
    def _create_endpoint_config(self, *args, **kwargs):
        self.ensure_one()
        return self.client.create_endpoint_config(**kwargs)

    # Container #

    @api.multi
    def get_containers(self, **kwargs):
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
        if kwargs.get('host_config'):
            kwargs['host_config'] = self._create_host_config(
                **kwargs['host_config'])
        if kwargs.get('networking_config'):
            networking_config = {network: self._create_endpoint_config(
                **endpoint_config) for network, endpoint_config
                in kwargs['networking_config'].items()}
            kwargs['networking_config'] = self._create_networking_config(
                networking_config)
        _logger.debug(repr(kwargs))
        return self.client.create_container(**kwargs)

    @api.multi
    def start_container(self, container):
        self.ensure_one()
        _logger.info('Starting container %s...' % container)
        try:
            self.client.start(container)
        except Exception as e:
            raise UserError(_("Starting container %s failed\n\n%s")
                            % (container, get_exception_message(e)))
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
        containers = list(map(
            lambda container: container['Names'][0].replace('/', ''),
            containers))
        if 'v' not in kwargs:  # Remove the volumes associated to the container
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
            cmd = list(map(str, cmd))
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
        kwargs = {}
        if LooseVersion(docker.__version__) >= LooseVersion('3.1.0'):
            kwargs['chunk_size'] = 1024 * 1024  # 1MB
        strm, stat = self.client.get_archive(container, path, **kwargs)
        _logger.debug(stat)
        return strm

    @api.multi
    def get_stats(self, container, **kwargs):
        self.ensure_one()
        _logger.debug('Getting stats for container %s...' % container)
        kwargs['container'] = container
        _logger.debug(repr(kwargs))
        return self.client.stats(**kwargs)

    @api.multi
    def get_logs(self, container, **kwargs):
        self.ensure_one()
        _logger.debug('Getting logs for container %s...' % container)
        kwargs['container'] = container
        _logger.debug(repr(kwargs))
        return self.client.logs(**kwargs)

    @api.multi
    def get_running_processes(self, container, **kwargs):
        self.ensure_one()
        _logger.debug('Getting running processes for container %s...'
                      % container)
        kwargs['container'] = container
        _logger.debug(repr(kwargs))
        return self.client.top(**kwargs)

    # Image #

    @api.multi
    def get_images(self, **kwargs):
        _logger.debug(repr(kwargs))
        images = []
        for docker_host in self:
            images.extend(docker_host.client.images(**kwargs))
        return images

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
        error = all_lines[-1].get('error') or ''
        if error:
            raise UserError(_("Building image %s failed\n\n%s") % (tag, error))
        return '\n'.join(map(str, all_lines))

    @api.multi
    def pull_image(self, repository, **kwargs):
        self.ensure_one()
        _logger.info('Pulling image %s towards %s...'
                     % (repository, self.display_name))
        for image in self.client.images(all=True):
            if repository in (image.get('RepoTags') or []):
                return image
        kwargs['repository'], kwargs['tag'] = format_repository_and_tag(
            repository)
        return self.client.pull(**kwargs)

    @api.multi
    def tag_image(self, image, tags=None, **kwargs):
        self.ensure_one()
        tags = tags or 'latest'
        if isinstance(tags, string_types):
            tags = [tags]
        kwargs['image'] = image
        if kwargs.get('repository'):
            kwargs['repository'] = format_repository(kwargs['repository'])
        for tag in tags:
            kwargs['tag'] = tag
            new_tag = '%s:%s' % (kwargs['repository'], tag) \
                      if kwargs.get('repository') else tag
            _logger.info('Tagging image %s as %s...' % (image, new_tag))
            _logger.debug(repr(kwargs))
            self.client.tag(**kwargs)
        return True

    @api.multi
    def push_image(self, repository, **kwargs):
        self.ensure_one()
        repository = format_repository(repository)
        _logger.info('Pushing image %s from %s...'
                     % (repository, self.display_name))
        kwargs['repository'] = format_repository(repository)
        _logger.debug(repr(kwargs))
        return self.client.push(**kwargs)

    @api.multi
    def remove_image(self, image, **kwargs):
        self.ensure_one()
        _logger.info('Removing image %s from %s...'
                     % (image, self.display_name))
        if self.client.images(name=image, all=True):
            kwargs['image'] = image
            _logger.debug(repr(kwargs))
            self.client.remove_image(**kwargs)
        return True

    @api.one
    def _purge_images(self):
        _logger.info('Purging unused images for %s...' % self.display_name)
        for image in self.client.images(quiet=True,
                                        filters={'dangling': True}):
            self.client.remove_image(image, force=True)

    @api.model
    def purge_images(self):
        self.search([])._purge_images()
        return True

    # Network #

    @api.multi
    def get_networks(self, **kwargs):
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
    def remove_network(self, network, force=False):
        self.ensure_one()
        if isinstance(network, dict):
            network = network['Id']
        _logger.info('Removing network %s...' % network)
        _logger.debug(network)
        if force or self.get_networks(names=[network]):
            self.client.remove_network(network)
        return True

    @api.multi
    def clean_networks(self):
        # Try to remove all networks
        self.ensure_one()
        for network in self.get_networks():
            try:
                self.remove_network(network, force=True)
            except Exception:
                pass  # Ignore failure when network has linked containers
        return True

    # Volume #

    @api.multi
    def get_volumes(self, **kwargs):
        self.ensure_one()
        _logger.debug(repr(kwargs))
        return self.client.volumes(**kwargs)['Volumes']

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
        if self.get_volumes(filters={'name': volume}):
            self.client.remove_volume(volume)
        return True

    # Stats #

    @api.multi
    def update_stats(self):
        self.ensure_one()
        data = {}
        containers = self.get_containers()
        container_names = [
            name[1:]
            for cont in containers
            for name in cont['Names']
            if '/' not in name[1:]
        ]
        for container in container_names:
            stats_gen = self.get_stats(container, decode=True)
            pstats = stats_gen.next()
            stats = stats_gen.next()
            data[container] = [
                '%.2f %%' % (
                    (stats['cpu_stats']['cpu_usage']['total_usage'] -
                     pstats['cpu_stats']['cpu_usage']['total_usage']) * 100.0 /
                    (stats['cpu_stats']['system_cpu_usage'] -
                     pstats['cpu_stats']['system_cpu_usage'])),
                '%s / %s' % (b2human(stats['memory_stats']['usage']),
                             b2human(stats['memory_stats']['limit'])),
                '%.2f %%' % (stats['memory_stats']['usage'] * 100.0 /
                             stats['memory_stats']['limit']),
                '%.2f %%' % (stats['memory_stats']['max_usage'] * 100.0 /
                             stats['memory_stats']['limit']),
                '%s / %s' % (b2human(sum(network['rx_bytes'] for network
                                         in stats['networks'].values())),
                             b2human(sum(network['tx_bytes'] for network
                                         in stats['networks'].values()))),
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
                % (container, ''.join(map(
                    lambda value: '<td>%s</td>' % value, data[container])))
        self.stats = '<table class="o_list_view table table-condensed' \
                     ' table-striped">%s%s</table>' % (thead, tbody)
        self.stats_containers = len(container_names)
        self.stats_date = fields.Datetime.now()
        return True

    @api.multi
    def show_current_stats(self):
        self.update_stats()
        view = self.env.ref('smile_docker.view_docker_host_stats_form')
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
