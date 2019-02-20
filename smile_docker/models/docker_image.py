# -*- coding: utf-8 -*-

import logging
import sys
from threading import Thread

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval

from ..tools import format_container, format_image, format_repository, \
    format_repository_and_tag, lock, with_new_cursor

if sys.version_info > (3,):
    long = int

_logger = logging.getLogger(__name__)


class DockerImage(models.Model):
    _name = 'docker.image'
    _description = 'Docker Image'
    _inherit = 'docker.build'
    _order = 'sequence,id'
    _directory_prefix = 'image'

    @api.model
    def _get_default_docker_registry(self):
        return self.env['docker.registry'].sudo().search([], limit=1)

    @api.one
    def _get_docker_registry_image(self):
        self.docker_registry_image = self.docker_registry_id. \
            get_registry_image(self.docker_image)

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    docker_registry_id = fields.Many2one(
        'docker.registry', 'Docker registry', required=True,
        default=_get_default_docker_registry)
    docker_host_id = fields.Many2one(
        related='docker_registry_id.docker_host_id', readonly=True)
    docker_registry_image = fields.Char(compute='_get_docker_registry_image')
    default_environment = fields.Text()
    default_host_config = fields.Text()
    healthcheck = fields.Text(default="{'disable': True}")
    with_persistent_storage = fields.Boolean()
    link_ids = fields.One2many(
        'docker.link', 'base_image_id', 'Linked services')
    is_in_registry = fields.Boolean(readonly=True, copy=False)
    build_on_the_fly = fields.Boolean()

    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)', 'Name must be unique'),
        ('unique_docker_image', 'UNIQUE(docker_image, docker_registry_id)',
         'Docker image must be unique by Docker registry'),
    ]

    # Link #

    @api.multi
    def get_all_links(self, only_with_persistent_storage=False):
        self.ensure_one()
        all_links = self.env['docker.link']
        links = self.link_ids
        while links:
            all_links |= links
            links = links.mapped('linked_image_id.link_ids')
        if only_with_persistent_storage:
            all_links = all_links.filtered(
                lambda link: link.linked_image_id.with_persistent_storage)
        return all_links[::-1]

    # Image #

    @api.multi
    def write(self, vals):
        self._check_to_delete_from_registry(vals)
        return super(DockerImage, self).write(vals)

    _docker_fields = ['active', 'docker_image', 'dockerfile']

    @api.multi
    def _check_to_delete_from_registry(self, vals):
        for field in self._docker_fields:
            if field in vals:
                self._delete_from_registry(to_recreate=True)
                break

    @api.multi
    def unlink(self):
        self._delete_from_registry()
        return super(DockerImage, self).unlink()

    @api.one
    def _delete_from_registry(self, to_recreate=False):
        if self.docker_registry_image and \
                self.docker_registry_image != self.docker_image:
            self.docker_host_id.remove_image(self.docker_registry_image)
            if not to_recreate:
                repository, tag = format_repository_and_tag(self.docker_image)
                image = format_image(repository)
                self.docker_registry_id.delete_image(image, tag)
            self.is_in_registry = False

    @api.model
    def _get_images_to_store_domain(self):
        return [('is_in_registry', '=', False),
                ('build_on_the_fly', '=', False)]

    @api.multi
    def store_in_registry(self):
        if not self:  # Scheduled action
            domain = self._get_images_to_store_domain()
            self = self.search(domain)
        # else:  # Button
        #     self.filtered(
        #       lambda image: image.is_in_registry)._delete_from_registry()
        for image in self:
            thread = Thread(target=image._store_in_registry_locked)
            thread.start()
        return True

    @api.one
    @with_new_cursor()
    @lock('Storing in registry already in progress for image %(name)s')
    def _store_in_registry_locked(self):
        self._store_in_registry()

    @api.one
    def _store_in_registry(self):
        if self.docker_registry_image != self.docker_image:
            repository, tag = format_repository_and_tag(self.docker_image)
            # image = format_image(repository)
            # self.docker_registry_id.delete_image(image, tag)
            self.create_image()
            if ':' in self.docker_image:
                tag = self.docker_image.split(':')[-1]
                repository = self.docker_registry_image[:-len(tag) - 1]
            else:
                repository, tag = self.docker_registry_image, ''
            self.docker_host_id.tag_image(
                self.docker_image, tags=tag, repository=repository)
            self.docker_host_id.push_image(self.docker_registry_image)
            self.docker_host_id.remove_image(self.docker_image)
        self.is_in_registry = True

    @api.multi
    def _get_image_infos(self, suffix='', environment=None, volume_from=''):
        self.ensure_one()
        infos = {
            'image': self.docker_registry_image,
            'environment': safe_eval(self.default_environment or '{}'),
        }
        if environment:
            infos['environment'].update(environment)
        if volume_from:
            infos['volumes'] = [volume_from]
        volumes_from, links = [], []
        for link in self.link_ids:
            if link.volume_from:
                volumes_from.append(format_container(link.name, suffix))
            else:
                links.append(link.name)
        if volumes_from:
            infos['volumes_from'] = volumes_from
        if links:
            infos['links'] = links
        return infos

    # Container #

    @api.multi
    def _get_container_infos(self, docker_host, name, suffix='', image=None,
                             labels=None, environment=None, host_config=None,
                             volume_from='', network=None, aliases=None):
        params = self._get_image_infos(suffix, environment, volume_from)
        if image:
            params['image'] = image
        for key in ('links', 'volumes_from'):
            if key in params:
                del params[key]
        params['name'] = format_container(name, suffix)
        params['detach'] = True
        params['labels'] = labels or {}
        if host_config:
            params['host_config'] = host_config
        if network:
            params['networking_config'] = {network: {
                'aliases': aliases or [name]}}
        return params

    @api.multi
    def create_container(self, docker_host, name, suffix='', image=None,
                         labels=None, environment=None, host_config=None,
                         volume_from='', network=None, aliases=None,
                         create_network=False):
        self.ensure_one()
        container_name = format_container(name, suffix)
        if isinstance(docker_host, (int, long)):
            docker_host = self.env['docker.host'].browse(docker_host)
        if create_network:
            tries = 2
            while tries:
                try:
                    docker_host.create_network(container_name)
                    break
                except Exception:  # Because too many unused networks
                    docker_host.clean_networks()
                    tries -= 1
            network = container_name
        config = safe_eval(self.default_host_config or '{}')
        if host_config:
            config.update(host_config)
        for link in self.link_ids:
            params = {
                'docker_host': docker_host,
                'name': link.name,
                'suffix': suffix,
                'environment': safe_eval(link.environment or '{}'),
                'host_config': safe_eval(link.host_config or '{}'),
                'volume_from': link.volume_from,
                'network': network,
            }
            container = link.linked_image_id.create_container(**params)
            if link.volume_from:
                config.setdefault('volumes_from', []).append(container)
            else:
                config.setdefault('links', []).append((container, link.name))
        params = self._get_container_infos(docker_host, name, suffix, image,
                                           labels, environment, config,
                                           volume_from, network, aliases)
        if self.build_on_the_fly:
            self.create_image()
        else:
            docker_host.pull_image(params['image'])
        docker_host.create_container(**params)
        return container_name

    # Service #

    @api.multi
    def get_service_infos(self, name='', suffix='', repository='', tag='',
                          ports=None, environment=None, volume_from=None,
                          with_persistent_storage=True):
        self.ensure_one()
        infos = self._get_image_infos(
            environment=environment, volume_from=volume_from)
        name = name or format_image(self.docker_image)
        infos['container_name'] = format_container(name, suffix)
        infos['healthcheck'] = safe_eval(self.healthcheck) \
            if self.healthcheck else {'disable': True}
        if self.with_persistent_storage is with_persistent_storage and \
                repository:
            infos['image'] = '%s_%s' % (format_repository(repository), name)
            if tag:
                infos['image'] += ':%s' % tag
        if ports:
            infos['ports'] = ports
        if 'links' in infos:
            del infos['links']
        if self.link_ids:
            infos['depends_on'] = {
                link.name: {'condition': 'service_healthy'}
                for link in self.link_ids
            }
        services = {name: infos}
        for link in self.link_ids:
            params = {
                'name': link.name,
                'suffix': suffix,
                'repository': repository,
                'tag': tag,
                'environment': link.environment,
                'volume_from': link.volume_from,
                'with_persistent_storage': with_persistent_storage,
            }
            services.update(link.linked_image_id.get_service_infos(**params))
        return services
