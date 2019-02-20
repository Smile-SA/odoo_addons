# -*- coding: utf-8 -*-

import inspect
import json
import logging
import os.path
import shutil
from threading import Thread
import yaml

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from ..tools import call, format_container, format_image, \
    get_exception_message, secure

_logger = logging.getLogger(__name__)


class DockerContainer(models.AbstractModel):
    _name = 'docker.container'
    _description = 'Docker Container'
    _inherit = 'docker.build'
    _directory_prefix = 'container'

    @api.one
    def _get_docker_container(self):
        name = format_image(self.docker_image)
        self.docker_container = format_container(name, self.id)

    id = fields.Integer(readonly=True)
    docker_container = fields.Char(compute='_get_docker_container')
    auto_run = fields.Boolean('Auto-run')

    @api.multi
    def is_alive(self, all=False):
        self.ensure_one()
        return bool(self.docker_host_id.get_containers(
            all=all, filters={'name': self.docker_container}))

    @api.multi
    def remove_container(self, remove_image=False):
        for container in self:
            if container.is_alive(all=True):
                container_name = container.docker_container
                docker_host = container.docker_host_id
                secure(docker_host.remove_container)(
                    container_name, force=True)
                # Remove network created via
                # DockerImage.create_container(create_network)
                secure(docker_host.remove_network)(container_name)
                # Remove network created via
                # DockerContainer.start_container_from_registry
                secure(docker_host.remove_network)(
                    ''.join(c for c in container_name
                            if c.isalnum()) + '_default')
                if remove_image:
                    secure(docker_host.remove_image)(container.docker_image)
        return True

    @api.multi
    def _get_create_container_params(self):
        self.ensure_one()
        return {
            'image': self.docker_image,
            'name': self.docker_container,
            'detach': True,
        }

    @api.multi
    def create_container(self):
        self.ensure_one()
        _logger.info('Creating container %s...' % self.docker_container)
        self.create_image()
        params = self._get_create_container_params()
        return self.docker_host_id.create_container(**params)

    @api.multi
    def start_container(self):
        for container in self:
            if not container.is_alive(all=True):
                container.create_container()
            if not container.is_alive():
                container.docker_host_id.start_container(
                    container.docker_container)
        return True

    @api.multi
    def stop_container(self):
        for container in self:
            if container.is_alive():
                container.docker_host_id.stop_container(
                    container.docker_container)
        return True

    @api.multi
    def restart_container(self, force_recreate=True):
        if force_recreate:
            self.remove_container()
        else:
            self.stop_container()
        return self.start_container()

    @api.multi
    def _get_commit_params(self):
        self.ensure_one()
        return [{
            'container': self.docker_container,
            'repository': self.docker_image,
        }]

    @api.multi
    def commit_container(self, tag=''):
        for container in self:
            for params in container._get_commit_params():
                params['tag'] = tag or 'latest'
                container.docker_host_id.commit_container(**params)
        return True

    @api.multi
    def _get_tag_params(self):
        params_list = self._get_commit_params()
        for params in params_list:
            del params['container']
            params.update({
                'image': params['repository'],
                'force': True,
            })
        return params_list

    @api.multi
    def tag_image(self, tags=None):
        for container in self:
            for params in container._get_tag_params():
                params['tags'] = tags or ['latest']
                container.docker_host_id.tag_image(**params)
        return True

    @api.multi
    def _get_push_params(self):
        params_list = []
        for params in self._get_commit_params():
            params_list.append({'repository': params['repository']})
        return params_list

    @api.multi
    def push_image(self):
        for container in self:
            for params in container._get_push_params():
                container.docker_host_id.push_image(**params)
        return True

    @api.multi
    def remove_image(self, tags=None):
        for container in self:
            for params in container._get_push_params():
                image = params['repository']
                for tag in (tags or ['latest']):
                    container.docker_host_id.remove_image(
                        '%s:%s' % (image, tag))
        return True

    @api.multi
    def store_in_registry(self, tags=None):
        tag = tags and tags[0] or ''
        self.commit_container(tag)
        self.tag_image(tags)
        self.push_image()
        self.remove_image(tags)
        return True

    @api.multi
    def delete_from_registry(self, tags=None):
        for container in self:
            for params in container._get_push_params():
                image = format_image(params['repository'])
                for tag in (tags or ['latest']):
                    container.image_id.docker_registry_id.delete_image(
                        image, tag)
        return True

    @api.multi
    def get_service_infos(self, tag='', ports=None):
        self.ensure_one()
        image = self.docker_image
        if tag:
            image = '%s:%s' % (image.split(':')[0], tag)
        infos = {'image': image, 'container_name': self.docker_container}
        if ports:
            infos['ports'] = ports
        name = format_container(self.name)
        return {name: infos}

    @api.multi
    def start_container_from_registry(self, tag='', ports=None):
        for container in self:
            _logger.info('Starting container %s...' % self.docker_container)
            container._make_directory()
            try:
                filepath = os.path.join(
                    container.build_directory, 'docker-compose.yml')
                services = container.get_service_infos(tag, ports)
                content = yaml.dump(yaml.load(json.dumps(
                    {'version': '2.1', 'services': services})))
                _logger.debug(content)
                with open(filepath, 'w') as f:
                    f.write(content)
                try:
                    cmd = ['docker-compose', '-H',
                           container.docker_host_id.base_url, 'up', '-d']
                    call(cmd, container.build_directory)
                except Exception as e:
                    raise UserError(_('Starting container #%s failed\n\n%s')
                                    % (container.id, get_exception_message(e)))
            except Exception:
                raise
            finally:
                container._remove_directory()
        return True

    @api.model
    def _setup_complete(self):
        super(DockerContainer, self)._setup_complete()
        callers = [frame[3] for frame in inspect.stack()]
        if 'preload_registries' in callers:
            try:
                # Removing directories
                # if linked containers don't exist anymore
                directories = self.search([]).mapped('build_directory')
                builds_path = self.env['docker.host'].builds_path
                for dirname in os.listdir(builds_path):
                    dirpath = os.path.join(builds_path, dirname)
                    if dirname.startswith(self._directory_prefix) and \
                            dirpath not in directories:
                        _logger.info('Removing %s' % dirpath)
                        thread = Thread(
                            target=shutil.rmtree, args=(dirpath,))
                        thread.start()
                # Starting auto-run containers if not running
                _logger.info("Checking registry containers are running")
                self.search([('auto_run', '=', True)]).start_container()
            except Exception as e:
                _logger.error(get_exception_message(e))
