# -*- coding: utf-8 -*-

from odoo import api, models


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def _get_action_url(self, **kwargs):
        kwargs['base_url'] = self.env["ir.config_parameter"].get_param(
            'web.base.url')
        return "%(base_url)s/web?#id=%(res_id)s&view_type=%(view_type)s" \
            "&model=%(model)s&action=%(action_id)s" % kwargs
