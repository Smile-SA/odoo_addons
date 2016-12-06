# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class DockerLink(models.Model):
    _name = 'docker.link'
    _description = 'Docker Link'

    name = fields.Char(required=True)
    base_image_id = fields.Many2one('docker.image', 'Base image')
    branch_id = fields.Many2one('scm.repository.branch', 'Branch')
    linked_image_id = fields.Many2one('docker.image', 'Linked image', required=True)
    environment = fields.Text()
    host_config = fields.Text()
    volume_from = fields.Char('Data volume')

    _sql_constraints = [
        ('check_link', 'CHECK(base_image_id OR branch_id)', _('Please specify a base image or a branch')),
    ]

    @api.one
    @api.constrains('linked_image_id', 'base_image_id')
    def _check_links_tree(self):
        child_images = self.linked_image_id
        child_links = child_images.mapped('link_ids')
        while child_links:
            if child_links.mapped('linked_image_id') & child_images:
                raise ValidationError(_("You cannot create recursive linked services."))
            child_images |= child_links.mapped('linked_image_id')
            child_links = child_links.mapped('linked_image_id.link_ids')

    @api.multi
    def get_all_links(self, only_with_persistent_storage=False):
        all_links = self.browse()
        links = self.mapped('branch_id.link_ids') | self.mapped('base_image_id.link_ids')
        while links:
            for link in links:
                all_links |= link
            links = links.mapped('linked_image_id.link_ids')
        if only_with_persistent_storage:
            all_links = all_links.filtered(lambda link: link.linked_image_id.with_persistent_storage)
        return all_links[::-1]

    @api.multi
    def _get_image_infos(self, suffix=''):
        self.ensure_one()
        linked_image = self.linked_image_id
        infos = {'image': linked_image.docker_registry_image}
        if self.environment or linked_image.default_environment:
            infos['environment'] = safe_eval(linked_image.default_environment or '{}')
            infos['environment'].update(safe_eval(self.environment or '{}'))
        if self.volume_from:
            infos['volumes'] = [self.volume_from]
        volumes_from, links = [], []
        for link in linked_image.link_ids:
            if link.volume_from:
                volumes_from.append(link.name + suffix)
            else:
                links.append(link.name)
        if volumes_from:
            infos['volumes_from'] = volumes_from
        if links:
            infos['links'] = links
        return infos

    @api.multi
    def create_container(self, docker_host, suffix='', labels=None, network=None, add_container_name=False):
        self.ensure_one()
        if isinstance(docker_host, (int, long)):
            docker_host = self.env['docker.host'].browse(docker_host)
        name = self.name + suffix
        _logger.info('Creating container %s...' % name)
        params = self._get_image_infos(suffix)
        params['name'] = name
        if add_container_name:
            params['container_name'] = self.name
        params['detach'] = True
        params['labels'] = labels or {}
        if network:
            params['networking_config'] = docker_host.create_networking_config({
                network: docker_host.create_endpoint_config(aliases=[self.name])
            })
        config = {}
        for link in self.linked_image_id.link_ids:
            config.update(safe_eval(self.linked_image_id.default_host_config or '{}'))
            container = link.create_container(docker_host, suffix, labels, network, add_container_name)
            if link.volume_from:
                config.setdefault('volumes_from', []).append(container)
            else:
                config.setdefault('links', []).append((container, link.name))
        config.update(safe_eval(self.host_config or '{}'))
        if config:
            params['host_config'] = docker_host.create_host_config(**config)
        for key in ('links', 'volumes_from'):
            if key in params:
                del params[key]
        if self.linked_image_id.build_on_the_fly:
            self.linked_image_id._store_in_registry()
        docker_host.pull_image(params['image'])
        docker_host.create_container(**params)
        return params['name']

    @api.multi
    def get_service_infos(self, image_base, tag, add_container_name=False):
        services = {}
        for link in self:
            infos = link._get_image_infos()
            if link.linked_image_id.with_persistent_storage:
                infos['image'] = '%s_%s:%s' % (image_base, self.name, tag)
            if 'links' in infos:
                del infos['links']
            services[link.name] = infos
            services.update(link.linked_image_id.link_ids.get_service_infos(image_base, tag, add_container_name))
        return services
