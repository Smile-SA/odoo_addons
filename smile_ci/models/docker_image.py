# -*- coding: utf-8 -*-

from odoo import api, fields, models


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

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    docker_image = fields.Char(required=True)
    docker_registry_id = fields.Many2one('docker.registry', 'Docker registry', required=True,
                                         default=_get_default_docker_registry)
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
    def _store_in_registry(self):
        if self.active and self.docker_image and self.docker_image != self.docker_registry_image:
            self.docker_registry_id.delete_image(*self.docker_image.split(':'))
            docker_host = self.docker_registry_id.docker_host_id
            docker_host.pull_image(self.docker_image)
            tag = self.docker_image.split(':')[-1]
            repository = self.docker_registry_image[:-len(tag) - 1]
            docker_host.tag_image(self.docker_image, tags=tag, repository=repository)
            docker_host.push_image(self.docker_registry_image)
            docker_host.remove_image(self.docker_image)

    @api.one
    def _delete_in_registry(self):
        if self.docker_registry_image and self.docker_registry_image != self.docker_image:
            self.docker_registry_id.docker_host_id.remove_image(self.docker_registry_image)
            self.docker_registry_id.delete_image(*self.docker_image.split(':'))
