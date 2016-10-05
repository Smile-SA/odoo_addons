# -*- coding: utf-8 -*-

from odoo import api, models


class Repository(models.Model):
    _inherit = 'scm.repository'

    @api.model
    def create(self, vals):
        return super(Repository, self.with_context(mail_create_nosubscribe=True)).create(vals)
