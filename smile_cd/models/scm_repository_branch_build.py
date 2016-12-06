# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Build(models.Model):
    _inherit = 'scm.repository.branch.build'

    use_in_ci = fields.Boolean(related='branch_id.use_in_ci', readonly=True)

    @api.multi
    def open_deployment_wizard(self):
        action = self.branch_id.open_deployment_wizard()
        action['context']['default_build_id'] = self.id
        return action
