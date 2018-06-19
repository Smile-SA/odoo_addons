# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class DockerLink(models.Model):
    _name = 'docker.link'
    _description = 'Docker Link'

    name = fields.Char(required=True)
    base_image_id = fields.Many2one('docker.image', 'Main image')
    linked_image_id = fields.Many2one(
        'docker.image', 'Linked image', required=True)
    environment = fields.Text()
    host_config = fields.Text()
    volume_from = fields.Char('Data volume')

    @api.one
    @api.constrains('linked_image_id', 'base_image_id')
    def _check_links_tree(self):
        child_images = self.linked_image_id
        child_links = child_images.mapped('link_ids')
        while child_links:
            if child_links.mapped('linked_image_id') & child_images:
                raise ValidationError(
                    _("You cannot create recursive linked services."))
            child_images |= child_links.mapped('linked_image_id')
            child_links = child_links.mapped('linked_image_id.link_ids')
