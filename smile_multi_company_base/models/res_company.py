# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def _get_all_children(self):
        all_children = self.browse()
        children = self
        while children:
            all_children |= children
            children = children.mapped('child_ids')
        return all_children
