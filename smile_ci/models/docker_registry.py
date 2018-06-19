# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DockerRegistry(models.Model):
    _inherit = 'docker.registry'

    branch_ids = fields.One2many(
        'scm.repository.branch', 'docker_registry_id', 'Branches',
        readonly=True)

    @api.multi
    def unlink(self):
        if self.branch_ids:
            raise UserError(
                _('You cannot delete a registry linked to branches!'))
        return super(DockerRegistry, self).unlink()
