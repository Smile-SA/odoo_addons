# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    allows_to_log_in = fields.Boolean(default=True)

    @api.multi
    def _get_all_children(self):
        all_children = self.browse()
        children = self
        while children:
            all_children |= children
            children = children.mapped('child_ids')
        return all_children.sorted()
