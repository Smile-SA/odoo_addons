# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class Module(models.Model):
    _inherit = "ir.module.module"

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        domain = [
            '|',
            ('name', operator, name),
            ('shortdesc', operator, name)
        ] + (args or [])
        recs = self.search(domain, limit=limit)
        return recs.name_get()
