# -*- coding: utf-8 -*-

import base64
import logging
import os.path
import shutil

from odoo import api, fields, models

from .scm_repository_branch_build import DOCKERFILE

_logger = logging.getLogger(__name__)


class DockerImage(models.Model):
    _name = 'docker.image'
    _description = 'Docker Image'

    @api.model
    def _get_default_docker_registry(self):
        return self.env['docker.registry'].sudo().search([], limit=1)

    @api.one
    @api.depends('docker_registry_id.url', 'docker_image')
    def _get_docker_registry_image(self):
        self.docker_registry_image = self.docker_registry_id.get_registry_image(self.docker_image)

    @api.one
    @api.depends('docker_host_id')
    def _get_build_directory(self):
        self.build_directory = os.path.join(self.docker_host_id.builds_path, 'image_%s' % self.id)

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    docker_image = fields.Char(required=True)
    dockerfile = fields.Binary()
    build_directory = fields.Char(compute='_get_build_directory')
    build_on_the_fly = fields.Boolean()
    docker_registry_id = fields.Many2one('docker.registry', 'Docker registry', required=True,
                                         default=_get_default_docker_registry)
    docker_host_id = fields.Many2one(related='docker_registry_id.docker_host_id', readonly=True)
    docker_registry_image = fields.Char(compute='_get_docker_registry_image')
    default_environment = fields.Text()
    default_host_config = fields.Text()
    link_ids = fields.One2many('docker.link', 'base_image_id', 'Linked services')
    with_persistent_storage = fields.Boolean()
    is_postgres = fields.Boolean()

    @api.model
    def create(self, vals):
        image = super(DockerImage, self).create(vals)
        if image.docker_image.split(':')[0] not in image.docker_registry_id.get_images():
            image._store_in_registry()
        return image

    @api.multi
    def write(self, vals):
        res = super(DockerImage, self).write(vals)
        if vals.get('docker_image') or vals.get('docker_registry_id') or vals.get('active'):
            self._store_in_registry()
        if 'active' in vals and not vals['active']:
            self._delete_in_registry()
        return res

    @api.multi
    def unlink(self):
        self._delete_in_registry()
        return super(DockerImage, self).unlink()

    @api.one
    def _make_build_directory(self):
        if self.build_directory and not os.path.exists(self.build_directory):
            os.makedirs(self.build_directory)

    @api.one
    def _remove_build_directory(self):
        if self.build_directory and os.path.exists(self.build_directory):
            shutil.rmtree(self.build_directory)

    @api.one
    def _create_dockerfile(self):
        _logger.info('Generating dockerfile for %s...' % self.docker_image)
        content = base64.b64decode(self.dockerfile)
        filepath = os.path.join(self.build_directory, DOCKERFILE)
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

    @api.one
    def _store_in_registry(self):
        if self.active and self.docker_registry_image != self.docker_image:
            self.docker_registry_id.delete_image(*self.docker_image.split(':'))
            docker_host = self.docker_host_id
            if self.dockerfile:
                self._make_build_directory()
                self._create_dockerfile()
                self._build_image()
                self._remove_build_directory()
            else:
                docker_host.pull_image(self.docker_image)
            if ':' in self.docker_image:
                tag = self.docker_image.split(':')[-1]
                repository = self.docker_registry_image[:-len(tag) - 1]
            else:
                repository, tag = self.docker_registry_image, ''
            docker_host.tag_image(self.docker_image, tags=tag, repository=repository)
            docker_host.push_image(self.docker_registry_image)
            docker_host.remove_image(self.docker_image)

    @api.multi
    def store_in_registry(self):
        self._store_in_registry()
        return True

    @api.one
    def _delete_in_registry(self):
        if self.docker_registry_image and self.docker_registry_image != self.docker_image:
            self.docker_host_id.remove_image(self.docker_registry_image)
            self.docker_registry_id.delete_image(*self.docker_image.split(':'))
