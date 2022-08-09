# -*- coding: utf-8 -*-
# (C) 2022 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ApiRestField(models.Model):
    _name = 'api.rest.field'
    _order = 'sequence'
    _rec_name = 'field_name'
    _description = "Api Rest Field"

    sequence = fields.Integer()
    path_id = fields.Many2one(
        'api.rest.path', required=True, ondelete='cascade')
    model_id = fields.Many2one(
        related="path_id.model_id", readonly=True)
    field_id = fields.Many2one(
        'ir.model.fields', required=True, ondelete='cascade',
        domain="["
               "('model_id', '=', model_id),"
               "]")
    field_name = fields.Char(
        related="field_id.name", readonly=True)
    description = fields.Char()
    force_required = fields.Boolean(
        related="field_id.required", readonly=True)
    required = fields.Boolean()
    default_value = fields.Char()

    @api.onchange('field_id')
    def _onchange_field_id(self):
        self.required = self.field_id.required

    @api.onchange('default_value')
    def _onchange_default_value(self):
        if self.default_value:
            self.required = False

    @api.onchange('required')
    def _onchange_required(self):
        if self.default_value:
            self.required = False
