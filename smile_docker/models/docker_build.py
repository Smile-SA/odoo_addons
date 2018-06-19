# -*- coding: utf-8 -*-

import base64
import logging
import os
import shutil

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class DockerBuild(models.AbstractModel):
    _name = 'docker.build'
    _description = 'Docker Build'
    _directory_prefix = ''

    @api.model
    def _get_default_docker_host(self):
        return self.env['docker.host'].get_default_docker_host().id

    @api.one
    @api.depends('docker_host_id')
    def _get_build_directory(self):
        directory_name = '%s_%s' % (self._directory_prefix, self.id)
        self.build_directory = os.path.join(
            self.docker_host_id.builds_path, directory_name)

    name = fields.Char(required=True)
    docker_image = fields.Char(required=True)
    dockerfile = fields.Binary(attachment=True)
    docker_host_id = fields.Many2one(
        'docker.host', 'Docker host', required=True,
        default=_get_default_docker_host)
    build_directory = fields.Char(compute='_get_build_directory')

    @api.multi
    def create_image(self):
        docker_hosts = self.mapped('docker_host_id')
        images = sum([i['RepoTags'] for i in docker_hosts.get_images()
                      if i['RepoTags']], [])
        for build in self:
            if build.docker_image in images:
                continue
            elif build.dockerfile:
                build._make_directory()
                build._create_dockerfile()
                build._build_image()
                build._remove_directory()
            else:
                build.docker_host_id.pull_image(self.docker_image)
        return True

    @api.one
    def _make_directory(self):
        if self.build_directory and not os.path.exists(self.build_directory):
            os.makedirs(self.build_directory)

    @api.one
    def _remove_directory(self):
        if self.build_directory and os.path.exists(self.build_directory):
            shutil.rmtree(self.build_directory)

    @api.one
    def _create_dockerfile(self):
        _logger.info('Generating Dockerfile for %s...' % self.docker_image)
        content = base64.b64decode(self.dockerfile)
        filepath = os.path.join(self.build_directory, 'Dockerfile')
        with open(filepath, 'w') as f:
            f.write(content)

    @api.multi
    def _get_build_params(self):
        self.ensure_one()
        return {
            'path': self.build_directory,
            'tag': self.docker_image,
        }

    @api.one
    def _build_image(self):
        params = self._get_build_params()
        self.docker_host_id.build_image(**params)
