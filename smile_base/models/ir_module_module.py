# -*- coding: utf-8 -*-
# (C) 2019 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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
