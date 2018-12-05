# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class IrModelTest(models.Model):
    _name = 'ir.model.test'
    _description = 'Test Model'

    name = fields.Char()
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')])
    copy_name = fields.Char(compute='_get_copy_name', store=True)

    @api.one
    @api.depends(('name', [('state', '=', 'draft')]))
    def _get_copy_name(self):
        self.copy_name = self.name
