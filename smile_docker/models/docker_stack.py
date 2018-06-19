# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models

from ..tools import format_container, format_repository

_logger = logging.getLogger(__name__)


class DockerStack(models.AbstractModel):
    _name = 'docker.stack'
    _description = 'Docker Stack'
    _inherit = 'docker.container'

    image_id = fields.Many2one(
        'docker.image', 'Docker image', required=True, ondelete='restrict')
    docker_image = fields.Char(related='image_id.docker_registry_image')

    @api.multi
    def _get_linked_container_names(self):
        self.ensure_one()
        names = []
        for link in self.image_id.get_all_links():
            names.append(format_container(link.name, self.id))
        names.append(self.docker_container)
        return names

    @api.multi
    def _is_alive(self, name, all=False):
        self.ensure_one()
        if self.docker_host_id.get_containers(all=all, filters={'name': name}):
            return True
        return False

    @api.multi
    def remove_container(self, remove_image=False):
        for container in self:
            for container_name in container._get_linked_container_names()[:-1]:
                if container._is_alive(container_name, all=True):
                    container.docker_host_id.remove_container(
                        container_name, force=True)
            super(DockerStack, container).remove_container(remove_image)
        return True

    @api.multi
    def _get_create_container_params(self):
        self.ensure_one()
        return {
            'name': self.docker_container,
            'suffix': self.id,
        }

    @api.multi
    def create_container(self):
        self.ensure_one()
        self.remove_container()
        try:
            params = self._get_create_container_params()
            if params.get('image') and \
                    params['image'] != self.image_id.docker_registry_image:
                self.create_image()
            return self.image_id.create_container(
                self.docker_host_id, **params)
        except Exception:
            self.remove_container()
            raise

    @api.multi
    def start_container(self):
        for container in self:
            if not container.is_alive(all=True):
                container.create_container()
            for container_name in container._get_linked_container_names():
                if not container._is_alive(container_name):
                    container.docker_host_id.start_container(container_name)
        return True

    @api.multi
    def stop_container(self):
        for container in self:
            for container_name in container._get_linked_container_names():
                if container._is_alive(container_name):
                    container.docker_host_id.stop_container(container_name)
        return True

    @api.multi
    def _get_commit_params(self):
        repository = format_repository(self.image_id.docker_registry_image)
        params = [{
            'container': format_container(link.name, self.id),
            'repository': '%s_%s' % (repository, link.name),
        } for link in self.image_id.get_all_links(
            only_with_persistent_storage=True)]
        params += [{
            'container': self.docker_container,
            'repository': repository,
        }]
        return params

    @api.multi
    def _get_service_infos_params(self, tag, ports):
        self.ensure_one()
        params = {
            'name': format_container(self.name),
            'suffix': self.id,
            'repository': format_repository(
                self.image_id.docker_registry_image),
            'tag': tag,
        }
        if ports:
            params['ports'] = ports
        return params

    @api.multi
    def get_service_infos(self, tag='', ports=None):
        self.ensure_one()
        params = self._get_service_infos_params(tag, ports)
        return self.image_id.get_service_infos(**params)
