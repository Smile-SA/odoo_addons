# -*- coding: utf-8 -*-

from odoo import api, fields, models


class DockerRegistryCleaning(models.TransientModel):
    _name = 'docker.registry.cleaning'
    _description = 'Docker Registry Cleaning'
    _rec_name = 'docker_registry_id'

    docker_registry_id = fields.Many2one(
        'docker.registry', 'Docker registry', required=True,
        readonly=True, ondelete='cascade')
    image_tag = fields.Char("Image tag to remove", required=True)

    @api.multi
    def run(self):
        self.ensure_one()
        image, tag = self.image_tag.split(':')
        self.docker_registry_id.delete_image(image, tag)
        return {'type': 'ir.actions.act_window_close'}
