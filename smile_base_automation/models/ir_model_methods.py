# -*- coding: utf-8 -*-
# (C) 2020 Smile (<http://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class IrModelMethods(models.Model):
    _name = 'ir.model.methods'
    _description = 'Model Method'
    _order = 'name'

    name = fields.Char(size=128, readonly=True, required=True, index=True)
    model_id = fields.Many2one('ir.model', 'Model', readonly=True,
                               required=True, index=True, ondelete='cascade')
    is_public = fields.Boolean(compute='_is_public', store=True)

    @api.depends('name')
    def _is_public(self):
        for method in self:
            method.is_public = not method.name.startswith('_')
