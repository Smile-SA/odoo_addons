# -*- coding: utf-8 -*-

from odoo import api, fields, models


class DockerRegistryImages(models.TransientModel):
    _name = 'docker.registry.wizard'
    _description = 'Docker Registry Images'
    _rec_name = 'registry_id'

    registry_id = fields.Many2one('docker.registry', 'Docker registry', required=True)
    images = fields.Html('Docker images', compute='_get_images')

    @api.one
    @api.depends('registry_id')
    def _get_images(self):
        content = {}
        for image in sorted(self.registry_id.get_images()):
            content[image] = sorted(self.registry_id.get_image_tags(image))
        thead = '<thead><tr><th>Image</th><th>Tags</th></tr></thead>'
        tbody = ''
        for image, tags in content.iteritems():
            tbody += '<tr><td>%s</td><td>%s</td></tr>' % (image, ', '.join(tags))
        self.images = '<table class="o_list_view table table-condensed table-striped">%s%s</table>' % (thead, tbody)
